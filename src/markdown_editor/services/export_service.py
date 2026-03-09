import os
import re

from .html_preview import HtmlPreviewService


class ExportService:
    @staticmethod
    def markdown_to_html(markdown_text, title="Markdown Document", render_style="default"):
        return HtmlPreviewService.render_document(
            markdown_text,
            title=title,
            render_style=render_style,
        )

    @staticmethod
    def export_html(file_path, markdown_text, title="Markdown Document"):
        output = ExportService.markdown_to_html(markdown_text, title=title)
        with open(file_path, "w", encoding="utf-8") as handle:
            handle.write(output)

    @staticmethod
    def normalize_image_path(image_path, base_dir=None):
        image_path = os.path.expanduser(image_path)
        if base_dir and not os.path.isabs(image_path):
            return os.path.normpath(os.path.join(base_dir, image_path))
        return image_path

    @staticmethod
    def extract_image_paths(markdown_text, base_dir=None):
        paths = []
        for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", markdown_text):
            image_path = match.group(1).strip().strip('"')
            paths.append(ExportService.normalize_image_path(image_path, base_dir))
        return paths
