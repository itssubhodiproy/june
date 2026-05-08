import asyncio
import logging
from dataclasses import dataclass

import httpx
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from app.clients.api_client import ApiClient
from app.clients.redis_client import RedisClient
from app.config import settings
from app.llm.client import LLMClient, create_llm_client
from app.llm.prompts import build_user_prompt, get_system_prompt
from app.llm.response_parser import ResponseValidationError, parse_llm_response
from app.rag.pipeline import RAGPipeline
from app.types import (
    CellCompletedEvent,
    CellErrorEvent,
    CellUpdatePayload,
    ExtractionManifestCell,
    ExtractionTask,
    RunCompletedEvent,
)


@dataclass
class HandlerDependencies:
    redis: RedisClient
    api: ApiClient


class ExtractionProcessingError(Exception):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
        cell: ExtractionManifestCell | None = None,
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.cell = cell


class ExtractionHandler:
    def __init__(self, deps: HandlerDependencies) -> None:
        self._deps = deps
        self._rag = RAGPipeline(deps.api)
        self._llm: LLMClient = create_llm_client()
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_EXTRACTIONS)

    async def handle(self, task: ExtractionTask) -> None:
        manifest = await self._deps.api.get_extraction_manifest(
            task.table_id,
            cell_id=task.cell_id, # this can also be null in case of bulk processing for a table
        )
        
        if not manifest.cells:
            await self._deps.redis.publish_run_completed(
                RunCompletedEvent(
                    type="run_completed",
                    table_id=task.table_id,
                    total=0,
                    completed=0,
                    failed=0,
                )
            )
            return

        completed_count = 0
        failed_count = 0

        processed = await asyncio.gather(
            *(self._process_cell(task.table_id, cell) for cell in manifest.cells),
            return_exceptions=True,
        )

        results: list[CellUpdatePayload] = []
        terminal_results: list[CellUpdatePayload] = []
        retryable_failures: list[ExtractionProcessingError] = []

        for cell, item in zip(manifest.cells, processed, strict=True):
            if isinstance(item, tuple):
                result, event = item
                results.append(result)
                if isinstance(event, CellCompletedEvent):
                    completed_count += 1
                else:
                    failed_count += 1
                continue

            if not isinstance(item, ExtractionProcessingError):
                logging.exception(
                    "Unexpected extraction failure for cell %s",
                    cell.cell_id,
                    exc_info=(type(item), item, item.__traceback__),
                )
                item = ExtractionProcessingError(
                    str(item),
                    retryable=True,
                    cell=cell,
                )

            if item.retryable:
                retryable_failures.append(item)
                continue

            result, event = self._build_error_result(
                task.table_id,
                item.cell or cell,
                str(item),
            )
            terminal_results.append(result)
            failed_count += 1
            await self._deps.redis.publish_cell_error(event)

        if results:
            await self._deps.api.bulk_update_cells(task.table_id, results)

        if terminal_results:
            await self._deps.api.bulk_update_cells(task.table_id, terminal_results)

        if retryable_failures and task.retry_count < settings.MAX_RETRIES:
            await self._enqueue_retryable_failures(task, retryable_failures)
            return

        exhausted_results: list[CellUpdatePayload] = []
        if retryable_failures:
            for failure in retryable_failures:
                failed_cell = failure.cell
                if failed_cell is None:
                    continue
                result, event = self._build_error_result(
                    task.table_id,
                    failed_cell,
                    str(failure),
                )
                exhausted_results.append(result)
                failed_count += 1
                await self._deps.redis.publish_cell_error(event)

        if exhausted_results:
            await self._deps.api.bulk_update_cells(task.table_id, exhausted_results)

        await self._deps.redis.publish_run_completed(
            RunCompletedEvent(
                type="run_completed",
                table_id=task.table_id,
                total=len(manifest.cells),
                completed=completed_count,
                failed=failed_count,
            )
        )

    async def handle_failure(
        self,
        task: ExtractionTask,
        error_message: str,
    ) -> None:
        manifest = await self._deps.api.get_extraction_manifest(
            task.table_id,
            cell_id=task.cell_id,
        )

        if not manifest.cells:
            return

        results: list[CellUpdatePayload] = []
        failed_count = 0
        for cell in manifest.cells:
            result, event = self._build_error_result(task.table_id, cell, error_message)
            results.append(result)
            failed_count += 1
            await self._deps.redis.publish_cell_error(event)

        await self._deps.api.bulk_update_cells(task.table_id, results)
        await self._deps.redis.publish_run_completed(
            RunCompletedEvent(
                type="run_completed",
                table_id=task.table_id,
                total=failed_count,
                completed=0,
                failed=failed_count,
            )
        )

    async def _process_cell(
        self,
        table_id: str,
        cell: ExtractionManifestCell,
    ) -> tuple[CellUpdatePayload, CellCompletedEvent | CellErrorEvent]:
        async with self._semaphore:
            try:
                rag_result = await self._rag.build_context(
                    document_id=cell.document_id,
                    column_prompt=cell.column_prompt,
                )

                if not rag_result.chunks:
                    result, event = self._build_not_found_result(table_id, cell)
                    await self._deps.redis.publish_cell_completed(event)
                    return result, event

                response = await self._llm.complete(
                    system_prompt=get_system_prompt(),
                    user_prompt=build_user_prompt(
                        column_prompt=cell.column_prompt,
                        column_type=cell.column_type,
                        context=rag_result.context,
                    ),
                )
                parsed = parse_llm_response(
                    response,
                    column_type=cell.column_type,
                    chunks=rag_result.chunks,
                )

                result = CellUpdatePayload(
                    cell_id=cell.cell_id,
                    status="completed",
                    answer=parsed.answer,
                    reasoning=parsed.reasoning,
                    source_references=parsed.source_references,
                )
                event = CellCompletedEvent(
                    type="cell_completed",
                    cell_id=cell.cell_id,
                    table_id=table_id,
                    document_id=cell.document_id,
                    column_id=cell.column_id,
                    answer=parsed.answer,
                    reasoning=parsed.reasoning,
                    source_references=parsed.source_references,
                )
                await self._deps.redis.publish_cell_completed(event)
                return result, event
            except (
                httpx.HTTPError,
                APIConnectionError,
                APITimeoutError,
                RateLimitError,
            ) as exc:
                raise ExtractionProcessingError(
                    str(exc),
                    retryable=True,
                    cell=cell,
                ) from exc
            except AuthenticationError as exc:
                raise ExtractionProcessingError(
                    str(exc),
                    retryable=False,
                    cell=cell,
                ) from exc
            except ResponseValidationError as exc:
                logging.warning("Cell %s failed validation: %s", cell.cell_id, exc)
                result, event = self._build_error_result(table_id, cell, str(exc))
                await self._deps.redis.publish_cell_error(event)
                return result, event
            except Exception as exc:
                logging.exception("Unexpected extraction error for cell %s", cell.cell_id)
                raise ExtractionProcessingError(
                    str(exc),
                    retryable=True,
                    cell=cell,
                ) from exc

    async def _enqueue_retryable_failures(
        self,
        task: ExtractionTask,
        failures: list[ExtractionProcessingError],
    ) -> None:
        retry_count = task.retry_count + 1
        retry_tasks = 0

        for failure in failures:
            if failure.cell is None:
                continue

            retry_tasks += 1
            await self._deps.redis.enqueue_extraction_task(
                ExtractionTask(
                    table_id=task.table_id,
                    type=task.type,
                    cell_id=failure.cell.cell_id,
                    retry_count=retry_count,
                )
            )

        logging.info(
            "Retrying %d extraction cell(s) for table %s (attempt %d/%d)",
            retry_tasks,
            task.table_id,
            retry_count,
            settings.MAX_RETRIES,
        )

    def _build_not_found_result(
        self,
        table_id: str,
        cell: ExtractionManifestCell,
    ) -> tuple[CellUpdatePayload, CellCompletedEvent]:
        answer = "Not found"
        reasoning = "No relevant content was retrieved for this question from the document."
        result = CellUpdatePayload(
            cell_id=cell.cell_id,
            status="completed",
            answer=answer,
            reasoning=reasoning,
            source_references=[],
        )
        event = CellCompletedEvent(
            type="cell_completed",
            cell_id=cell.cell_id,
            table_id=table_id,
            document_id=cell.document_id,
            column_id=cell.column_id,
            answer=answer,
            reasoning=reasoning,
            source_references=[],
        )
        return result, event

    def _build_error_result(
        self,
        table_id: str,
        cell: ExtractionManifestCell,
        error_message: str,
    ) -> tuple[CellUpdatePayload, CellErrorEvent]:
        result = CellUpdatePayload(
            cell_id=cell.cell_id,
            status="error",
            error_message=error_message,
        )
        event = CellErrorEvent(
            type="cell_error",
            cell_id=cell.cell_id,
            table_id=table_id,
            document_id=cell.document_id,
            column_id=cell.column_id,
            error=error_message,
        )
        return result, event
