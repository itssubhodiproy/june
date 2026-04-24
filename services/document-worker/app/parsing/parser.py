import asyncio
import json
import os
import tempfile
from abc import ABC, abstractmethod

from app.config import settings
from app.types import ParsedDocument, ParsedPage, ParsedTextItem


class DocumentParser(ABC):
    @abstractmethod
    async def parse(self, pdf_bytes: bytes) -> ParsedDocument:
        raise NotImplementedError


class LiteParseParser(DocumentParser):
    def __init__(self, dpi: int | None = None) -> None:
        self.dpi = dpi or settings.PARSER_DPI

    async def parse(self, pdf_bytes: bytes) -> ParsedDocument:
        from liteparse import LiteParse

        parser = LiteParse()
        result = await parser.parse_async(pdf_bytes, dpi=self.dpi)

        pages: list[ParsedPage] = []
        for index, page in enumerate(result.pages, start=1):
            items = [
                ParsedTextItem(
                    text=item.text,
                    x=item.x,
                    y=item.y,
                    width=item.width,
                    height=item.height,
                )
                for item in (page.textItems or [])
            ]

            pages.append(
                ParsedPage(
                    page_number=getattr(page, "pageNum", index),
                    text=page.text or "",
                    page_width=page.width,
                    page_height=page.height,
                    text_items=items,
                )
            )

        if not pages:
            raise ValueError("Parser returned no pages")

        return ParsedDocument(pages=pages)


class OpenDataLoaderParser(DocumentParser):
    async def parse(self, pdf_bytes: bytes) -> ParsedDocument:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        try:
            return await asyncio.to_thread(self._parse_sync, tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _parse_sync(self, path: str) -> ParsedDocument:
        from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

        loader = OpenDataLoaderPDFLoader(
            file_path=path,
            format="json",
            split_pages=True,
        )
        docs = loader.load()

        pages: list[ParsedPage] = []
        for doc in docs:
            page_data = json.loads(doc.page_content)
            page_number = doc.metadata.get("page", len(pages) + 1)

            items: list[ParsedTextItem] = []
            text_parts: list[str] = []

            for element in page_data.get("kids", []):
                content = element.get("content", "")
                if element.get("type") in ("paragraph", "heading", "list"):
                    text_parts.append(content)

                bbox = element.get("bounding box")  # [left, bottom, right, top]
                if bbox and content:
                    items.append(
                        ParsedTextItem(
                            text=content,
                            x=float(bbox[0]),
                            y=float(bbox[1]),
                            width=float(bbox[2] - bbox[0]),
                            height=float(bbox[3] - bbox[1]),
                        )
                    )

            page_width, page_height = self._compute_page_dims(items)
            pages.append(
                ParsedPage(
                    page_number=page_number,
                    text="\n".join(text_parts),
                    page_width=page_width,
                    page_height=page_height,
                    text_items=items,
                )
            )

        if not pages:
            raise ValueError("Parser returned no pages")

        return ParsedDocument(pages=pages)

    @staticmethod
    def _compute_page_dims(items: list[ParsedTextItem]) -> tuple[float, float]:
        if not items:
            return 612.0, 792.0  # US Letter default
        width = max((item.x + item.width for item in items), default=612.0)
        height = max((item.y + item.height for item in items), default=792.0)
        return width, height


def create_parser() -> DocumentParser:
    if settings.PARSER == "liteparse":
        return LiteParseParser()
    if settings.PARSER == "opendataloader":
        return OpenDataLoaderParser()
    raise ValueError(f"Unsupported parser: {settings.PARSER}")
