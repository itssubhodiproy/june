import asyncio
import logging
import signal

from app.clients.api_client import ApiClient
from app.clients.redis_client import RedisClient
from app.config import settings
from app.handler import ExtractionHandler, ExtractionProcessingError, HandlerDependencies
from app.types import ExtractionTask


class Consumer:
    _POP_TIMEOUT_SECONDS = 1

    def __init__(self) -> None:
        self._shutdown = asyncio.Event()

    async def run(self) -> None:
        redis = RedisClient()
        api = ApiClient()
        handler = ExtractionHandler(HandlerDependencies(redis=redis, api=api))

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler)

        logging.info("Consumer started, waiting for extraction tasks...")

        try:
            while not self._shutdown.is_set():
                try:
                    task = await redis.pop_extraction_task(
                        timeout=self._POP_TIMEOUT_SECONDS
                    )
                except asyncio.CancelledError:
                    break
                except Exception:
                    logging.exception("Queue pop failed; continuing")
                    await asyncio.sleep(1)
                    continue

                if task is None:
                    continue

                await self._process_task(task, redis, handler)
        finally:
            await redis.close()
            await api.aclose()
            logging.info("Consumer stopped")

    def _signal_handler(self) -> None:
        logging.info("Shutdown signal received")
        self._shutdown.set()

    async def _process_task(
        self,
        task: ExtractionTask,
        redis: RedisClient,
        handler: ExtractionHandler,
    ) -> None:
        try:
            await handler.handle(task)
        except ExtractionProcessingError as exc:
            if exc.retryable and task.retry_count < settings.MAX_RETRIES:
                await self._retry_task(task, redis)
            else:
                await self._report_terminal_failure(task, handler, str(exc))
        except Exception as exc:
            if task.retry_count < settings.MAX_RETRIES:
                await self._retry_task(task, redis)
            else:
                await self._report_terminal_failure(task, handler, str(exc))

    async def _retry_task(self, task: ExtractionTask, redis: RedisClient) -> None:
        retry_count = task.retry_count + 1

        logging.info(
            "Retrying extraction task for table %s (attempt %d/%d)",
            task.table_id,
            retry_count,
            settings.MAX_RETRIES,
        )

        retry_task = ExtractionTask(
            table_id=task.table_id,
            type=task.type,
            cell_id=task.cell_id,
            retry_count=retry_count,
        )
        await redis.enqueue_extraction_task(retry_task)

    async def _report_terminal_failure(
        self,
        task: ExtractionTask,
        handler: ExtractionHandler,
        error_message: str,
    ) -> None:
        try:
            await handler.handle_failure(task, error_message)
        except Exception:
            logging.exception(
                "Failed to report terminal extraction failure for table %s",
                task.table_id,
            )
        logging.error(
            "Extraction task for table %s failed permanently: %s",
            task.table_id,
            error_message,
        )
