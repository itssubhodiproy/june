import re

from app.types import BoundingBox, ChunkDraft, ParsedDocument, ParsedPage, ParsedTextItem


SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


class DocumentChunker:
    def __init__(self, target_tokens: int = 200, hard_cap_tokens: int = 500) -> None:
        self.target_tokens = target_tokens
        self.hard_cap_tokens = hard_cap_tokens

    def chunk(self, document: ParsedDocument) -> list[ChunkDraft]:
        chunks: list[ChunkDraft] = []
        chunk_index = 0

        for page in document.pages:
            page_chunks = self._chunk_page(page, start_index=chunk_index)
            chunks.extend(page_chunks)
            chunk_index += len(page_chunks)

        return chunks

    def _chunk_page(self, page: ParsedPage, *, start_index: int) -> list[ChunkDraft]:
        source_text = self._build_page_text(page)
        if not source_text.strip():
            return []

        item_ranges = self._build_item_ranges(page.text_items)
        sentence_ranges = self._split_sentences(source_text)

        chunks: list[ChunkDraft] = []
        current_start: int | None = None
        current_end: int | None = None
        current_tokens = 0

        for sentence_start, sentence_end in sentence_ranges:
            sentence_text = source_text[sentence_start:sentence_end].strip()
            if not sentence_text:
                continue

            sentence_tokens = self._estimate_tokens(sentence_text)
            if current_start is None:
                current_start = sentence_start
                current_end = sentence_end
                current_tokens = sentence_tokens
                continue

            next_tokens = current_tokens + sentence_tokens
            if current_tokens >= self.target_tokens or next_tokens > self.hard_cap_tokens:
                chunks.append(
                    self._build_chunk(
                        page=page,
                        source_text=source_text,
                        item_ranges=item_ranges,
                        start=current_start,
                        end=current_end or current_start,
                        chunk_index=start_index + len(chunks),
                    )
                )
                current_start = sentence_start
                current_end = sentence_end
                current_tokens = sentence_tokens
                continue

            current_end = sentence_end
            current_tokens = next_tokens

        if current_start is not None:
            chunks.append(
                self._build_chunk(
                    page=page,
                    source_text=source_text,
                    item_ranges=item_ranges,
                    start=current_start,
                    end=current_end or current_start,
                    chunk_index=start_index + len(chunks),
                )
            )

        return chunks

    def _build_chunk(
        self,
        *,
        page: ParsedPage,
        source_text: str,
        item_ranges: list[tuple[int, int, ParsedTextItem]],
        start: int,
        end: int,
        chunk_index: int,
    ) -> ChunkDraft:
        items = [
            item
            for item_start, item_end, item in item_ranges
            if item_end > start and item_start < end
        ]
        return ChunkDraft(
            chunk_index=chunk_index,
            text_content=source_text[start:end].strip(),
            page_number=page.page_number,
            section=None,
            bbox=BoundingBox(
                page_width=page.page_width,
                page_height=page.page_height,
                items=items,
            ),
        )

    def _build_page_text(self, page: ParsedPage) -> str:
        if page.text.strip():
            return page.text.strip()
        return " ".join(item.text.strip() for item in page.text_items if item.text.strip())

    def _split_sentences(self, text: str) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        last_index = 0
        for match in SENTENCE_BOUNDARY_RE.finditer(text):
            end = match.start()
            if end > last_index:
                ranges.append((last_index, end))
            last_index = match.end()
        if last_index < len(text):
            ranges.append((last_index, len(text)))
        return ranges

    def _estimate_tokens(self, text: str) -> int:
        return len(text.split())

    def _build_item_ranges(self, items: list[ParsedTextItem]) -> list[tuple[int, int, ParsedTextItem]]:
        ranges: list[tuple[int, int, ParsedTextItem]] = []
        cursor = 0
        for index, item in enumerate(items):
            item_text = item.text.strip()
            if not item_text:
                continue
            start = cursor
            end = start + len(item_text)
            ranges.append((start, end, item))
            cursor = end + (1 if index < len(items) - 1 else 0)
        return ranges
