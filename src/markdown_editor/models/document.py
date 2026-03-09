from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentHeader:
    level: int
    title: str
    line: int


@dataclass(frozen=True)
class DocumentStats:
    lines: int
    words: int
    characters: int
    size_bytes: int
    headers: int
    reading_time_minutes: int


@dataclass(frozen=True)
class PreviewBlock:
    kind: str
    text: str = ""
    language: str = ""
    rows: tuple[tuple[str, ...], ...] = ()
    alignments: tuple[str, ...] = ()
    items: tuple[tuple[int, bool, str], ...] = ()
    alt: str = ""
