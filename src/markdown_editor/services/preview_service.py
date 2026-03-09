import re

from ..models.document import PreviewBlock


class PreviewService:
    IMAGE_PATTERN = re.compile(r'^\s*!\[([^\]]*)\]\((.+)\)\s*$')
    TASK_PATTERN = re.compile(r'^(\s*)[-*]\s+\[([ xX])\]\s+(.*)$')
    BLOCKQUOTE_PATTERN = re.compile(r'^\s*>\s?(.*)$')
    LIST_PATTERN = re.compile(r'^(\s*)((?:[-*+])|(?:\d+\.))\s+(.*)$')
    THEMATIC_BREAK_PATTERN = re.compile(r'^\s{0,3}((\*\s*){3,}|(-\s*){3,}|(_\s*){3,})\s*$')

    @staticmethod
    def parse_blocks(text):
        lines = (text or "").splitlines()
        blocks = []
        markdown_buffer = []
        index = 0

        def flush_markdown():
            if not markdown_buffer:
                return
            chunk = "\n".join(markdown_buffer).strip("\n")
            markdown_buffer.clear()
            if chunk.strip():
                blocks.append(PreviewBlock(kind="markdown", text=chunk))

        while index < len(lines):
            line = lines[index]
            stripped = line.strip()

            if stripped.startswith("```"):
                flush_markdown()
                language = stripped[3:].strip()
                index += 1
                code_lines = []
                while index < len(lines) and not lines[index].strip().startswith("```"):
                    code_lines.append(lines[index])
                    index += 1
                if index < len(lines):
                    index += 1
                blocks.append(
                    PreviewBlock(
                        kind="code",
                        text="\n".join(code_lines),
                        language=language,
                    )
                )
                continue

            if PreviewService._is_thematic_break(line):
                flush_markdown()
                blocks.append(PreviewBlock(kind="rule"))
                index += 1
                continue

            if PreviewService._is_task_item(line):
                flush_markdown()
                items = []
                while index < len(lines):
                    task_match = PreviewService.TASK_PATTERN.match(lines[index])
                    if not task_match:
                        break
                    indent = len(task_match.group(1).replace("\t", "    "))
                    checked = task_match.group(2).lower() == "x"
                    items.append((indent, checked, task_match.group(3).strip()))
                    index += 1
                blocks.append(PreviewBlock(kind="tasks", items=tuple(items)))
                continue

            if PreviewService._is_list_item(line):
                flush_markdown()
                items = []
                while index < len(lines):
                    list_match = PreviewService.LIST_PATTERN.match(lines[index])
                    if not list_match or PreviewService._is_task_item(lines[index]):
                        break
                    indent = len(list_match.group(1).replace("\t", "    "))
                    bullet = list_match.group(2)
                    items.append((indent, bullet.endswith("."), f"{bullet} {list_match.group(3).strip()}"))
                    index += 1
                blocks.append(PreviewBlock(kind="list", items=tuple(items)))
                continue

            if PreviewService._is_blockquote_line(line):
                flush_markdown()
                quote_lines = []
                while index < len(lines):
                    quote_match = PreviewService.BLOCKQUOTE_PATTERN.match(lines[index])
                    if not quote_match:
                        break
                    quote_lines.append(quote_match.group(1))
                    index += 1
                blocks.append(PreviewBlock(kind="blockquote", text="\n".join(quote_lines).strip()))
                continue

            if PreviewService._is_table_start(lines, index):
                flush_markdown()
                table_lines = [lines[index], lines[index + 1]]
                index += 2
                while index < len(lines):
                    candidate = lines[index]
                    if not candidate.strip():
                        break
                    if "|" not in candidate:
                        break
                    table_lines.append(candidate)
                    index += 1
                rows, alignments = PreviewService._parse_table(table_lines)
                blocks.append(PreviewBlock(kind="table", rows=rows, alignments=alignments))
                continue

            image_match = PreviewService.IMAGE_PATTERN.match(line)
            if image_match:
                flush_markdown()
                image_path = PreviewService._extract_image_path(image_match.group(2))
                if image_path is None:
                    markdown_buffer.append(line)
                    index += 1
                    continue
                blocks.append(
                    PreviewBlock(
                        kind="image",
                        text=image_path,
                        alt=image_match.group(1).strip(),
                    )
                )
                index += 1
                continue

            markdown_buffer.append(line)
            index += 1

        flush_markdown()
        return blocks

    @staticmethod
    def _is_table_start(lines, index):
        if index + 1 >= len(lines):
            return False

        header = lines[index].strip()
        separator = lines[index + 1].strip()

        return "|" in header and PreviewService._is_table_separator(separator)

    @staticmethod
    def _is_task_item(line):
        return bool(PreviewService.TASK_PATTERN.match(line))

    @staticmethod
    def _is_blockquote_line(line):
        return bool(PreviewService.BLOCKQUOTE_PATTERN.match(line))

    @staticmethod
    def _is_list_item(line):
        return bool(PreviewService.LIST_PATTERN.match(line))

    @staticmethod
    def _is_thematic_break(line):
        return bool(PreviewService.THEMATIC_BREAK_PATTERN.match(line))

    @staticmethod
    def _is_table_separator(line):
        stripped = line.strip().strip("|")
        if not stripped:
            return False

        parts = [part.strip() for part in stripped.split("|")]
        if not parts:
            return False

        return all(re.fullmatch(r":?-{3,}:?", part) for part in parts)

    @staticmethod
    def _parse_table(lines):
        rows = []
        alignments = ()
        for line in lines:
            if PreviewService._is_table_separator(line.strip()):
                alignments = tuple(PreviewService._parse_table_alignments(line))
                continue
            rows.append(tuple(PreviewService._split_table_row(line)))
        return tuple(rows), alignments

    @staticmethod
    def _parse_table_alignments(line):
        stripped = line.strip().strip("|")
        alignments = []
        for part in [part.strip() for part in stripped.split("|")]:
            left = part.startswith(":")
            right = part.endswith(":")
            if left and right:
                alignments.append("center")
            elif right:
                alignments.append("right")
            else:
                alignments.append("left")
        return alignments

    @staticmethod
    def _split_table_row(line):
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        return [cell.strip() for cell in stripped.split("|")]

    @staticmethod
    def _extract_image_path(destination):
        cleaned = destination.strip()
        if not cleaned:
            return None

        if cleaned.startswith("<") and cleaned.endswith(">"):
            return cleaned[1:-1].strip()

        if cleaned[0] in {'"', "'"} and cleaned[-1] == cleaned[0]:
            return cleaned[1:-1].strip()

        title_match = re.match(r'^(?P<path><[^>]+>|"[^"]+"|\'[^\']+\'|\S+)\s+(?:"[^"]*"|\'[^\']*\'|\([^)]+\))\s*$', cleaned)
        if title_match:
            cleaned = title_match.group("path")

        if cleaned.startswith("<") and cleaned.endswith(">"):
            cleaned = cleaned[1:-1].strip()
        elif cleaned[0] in {'"', "'"} and cleaned[-1] == cleaned[0]:
            cleaned = cleaned[1:-1].strip()

        return cleaned or None
