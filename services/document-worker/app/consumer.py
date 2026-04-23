import asyncio
import logging
import signal

from app.clients.api_client import ApiClient
from app.clients.redis_client import RedisClient
from app.clients.s3_client import S3Client
from app.config import settings
from app.handler import DocumentHandler, DocumentProcessingError, HandlerDependencies
from app.types import DocumentParsingTask


class Consumer:
    _POP_TIMEOUT_SECONDS = 1

    def __init__(self) -> None:
        self._shutdown = asyncio.Event()

    async def run(self) -> None:
        redis = RedisClient()
        api = ApiClient()
        s3 = S3Client()
        handler = DocumentHandler(HandlerDependencies(redis=redis, s3=s3, api=api))

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler)

        logging.info("Consumer started, waiting for tasks...")

        try:
            while not self._shutdown.is_set():
                try:
                    task = await redis.pop_document_task(
                        timeout=self._POP_TIMEOUT_SECONDS
                    )
                except asyncio.CancelledError:
                    break

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
        task: DocumentParsingTask,
        redis: RedisClient,
        handler: DocumentHandler,
    ) -> None:
        try:
            await handler.handle(task)
        except DocumentProcessingError as exc:
            if exc.retryable and task.retry_count < settings.MAX_RETRIES:
                await self._retry_task(task, redis)
            else:
                await handler._handle_failure(
                    task.document_id,
                    task.table_id,
                )
                logging.error(
                    "Document %s failed: %s",
                    task.document_id,
                    exc,
                )
        except Exception:
            if task.retry_count < settings.MAX_RETRIES:
                await self._retry_task(task, redis)
            else:
                await handler._handle_failure(
                    task.document_id,
                    task.table_id,
                )
                logging.exception(
                    "Document %s failed permanently after %d retries",
                    task.document_id,
                    task.retry_count,
                )

    async def _retry_task(self, task: DocumentParsingTask, redis: RedisClient) -> None:
        retry_count = task.retry_count + 1

        logging.info(
            "Retrying document %s immediately (attempt %d/%d)",
            task.document_id,
            retry_count,
            settings.MAX_RETRIES,
        )

        retry_task = DocumentParsingTask(
            task_id=task.task_id,
            document_id=task.document_id,
            file_key=task.file_key,
            table_id=task.table_id,
            retry_count=retry_count,
        )
        await redis.enqueue_document_task(retry_task)
