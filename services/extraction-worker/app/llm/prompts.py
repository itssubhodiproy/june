from app.types import ColumnType


SYSTEM_PROMPT = """You are a legal document analyst. You extract specific information from legal documents with precision.
You always cite your sources.

Use only the provided document context.
Answer the question directly.
Include supporting citations from the provided chunks only.
Do not invent facts, citations, sections, or quotes.
If the answer is not present in the context, answer "Not found".
"""


COLUMN_TYPE_HINTS: dict[ColumnType, str] = {
    "free_response": "Respond with a concise summary.",
    "yes_no": "Respond with exactly 'Yes', 'No', or 'Not found'.",
    "date": "Respond with a date in YYYY-MM-DD format. If exact day is not available, answer 'Not found'.",
    "currency": "Respond with a dollar amount, a formula, or 'Not found'.",
    "verbatim": "Extract the exact text. Do not paraphrase.",
}


def get_system_prompt() -> str:
    return SYSTEM_PROMPT


def get_column_type_hint(column_type: ColumnType) -> str:
    return COLUMN_TYPE_HINTS[column_type]


def build_user_prompt(
    *,
    column_prompt: str,
    column_type: ColumnType,
    context: str,
) -> str:
    type_hint = get_column_type_hint(column_type)

    return f"""Document context:
---
{context}
---

Question: {column_prompt}
Response type: {column_type}
Type-specific instruction: {type_hint}
"""
