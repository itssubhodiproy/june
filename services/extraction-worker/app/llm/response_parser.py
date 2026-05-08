from datetime import date

from app.types import ColumnType, ParsedLLMResponse, RetrievedChunk


class ResponseValidationError(ValueError):
    pass


def parse_llm_response(
    response: ParsedLLMResponse,
    *,
    column_type: ColumnType,
    chunks: list[RetrievedChunk],
) -> ParsedLLMResponse:
    """
    Validates the LLM response against logical constraints.
    Note: Structural validation is handled by the SDK's structured output feature.
    """
    _validate_source_references(response, chunks)
    _validate_answer_type(response.answer, column_type, chunks)

    return response


def _validate_source_references(
    response: ParsedLLMResponse,
    chunks: list[RetrievedChunk],
) -> None:
    chunk_by_id = {chunk.id: chunk for chunk in chunks}

    if response.answer != "Not found" and not response.source_references:
        raise ResponseValidationError(
            "LLM response must include source references unless answer is 'Not found'"
        )

    for source in response.source_references:
        chunk = chunk_by_id.get(source.chunk_id)
        if chunk is None:
            raise ResponseValidationError(
                f"Unknown chunk_id in source reference: {source.chunk_id}"
            )

        if source.page != chunk.page_number:
            raise ResponseValidationError(
                f"Source reference page mismatch for chunk {source.chunk_id}"
            )


def _validate_answer_type(
    answer: str,
    column_type: ColumnType,
    chunks: list[RetrievedChunk],
) -> None:
    if answer == "Not found":
        return

    if column_type == "yes_no":
        if answer not in {"Yes", "No"}:
            raise ResponseValidationError("yes_no answer must be exactly 'Yes' or 'No'")
        return

    if column_type == "date":
        try:
            date.fromisoformat(answer)
        except ValueError as exc:
            raise ResponseValidationError(
                "date answer must be in YYYY-MM-DD format"
            ) from exc
        return

    if column_type == "currency":
        normalized = answer.replace("$", "").replace(",", "").strip()
        if any(char.isdigit() for char in normalized):
            return
        raise ResponseValidationError(
            "currency answer must contain a numeric value or be 'Not found'"
        )

    if column_type == "verbatim":
        chunk_texts = [chunk.text_content for chunk in chunks]
        if not any(answer in chunk_text for chunk_text in chunk_texts):
            raise ResponseValidationError(
                "verbatim answer must match provided chunk text"
            )
