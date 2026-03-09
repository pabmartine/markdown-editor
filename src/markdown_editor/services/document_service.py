import re

from ..core.i18n import translate as _
from ..models.document import DocumentHeader, DocumentStats


class DocumentService:
    @staticmethod
    def extract_headers(text):
        headers = []
        for index, line in enumerate(text.split("\n"), start=1):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue

            level = 0
            for char in stripped:
                if char == "#":
                    level += 1
                else:
                    break

            if level > 6:
                continue

            title = stripped[level:].strip()
            if title:
                headers.append(DocumentHeader(level=level, title=title, line=index))

        return headers

    @staticmethod
    def count_words(text):
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`[^`]*`", "", text)
        text = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", text)
        text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]*)\*", r"\1", text)
        text = re.sub(r"~~([^~]*)~~", r"\1", text)
        return len([word for word in text.split() if word.strip()])

    @staticmethod
    def compute_stats(text):
        normalized = text or ""
        headers = DocumentService.extract_headers(normalized)
        return DocumentStats(
            lines=len(normalized.split("\n")),
            words=DocumentService.count_words(normalized),
            characters=len(normalized),
            size_bytes=len(normalized.encode("utf-8")),
            headers=len(headers),
            reading_time_minutes=DocumentService.estimate_reading_time(normalized),
        )

    @staticmethod
    def estimate_reading_time(text, wpm=200):
        return max(1, round(DocumentService.count_words(text) / wpm))

    @staticmethod
    def generate_toc(text):
        headers = DocumentService.extract_headers(text)
        if not headers:
            return ""

        toc = [f"## {_('Table of Contents')}\n"]
        for header in headers:
            indent = "  " * (header.level - 1)
            anchor = header.title.lower().replace(" ", "-")
            anchor = re.sub(r"[^\w\-]", "", anchor)
            toc.append(f"{indent}- [{header.title}](#{anchor})")
        return "\n".join(toc) + "\n\n"

    @staticmethod
    def find_current_header(text, line_number):
        current_header = None
        for header in DocumentService.extract_headers(text):
            if header.line <= line_number:
                current_header = header
            else:
                break
        return current_header
