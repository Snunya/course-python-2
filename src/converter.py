"""Module converting DOCX documents to Markdown format via Pandoc."""

import subprocess


def convert_docx_to_markdown(docx_path: str) -> str:
    """Converts DOCX file to Markdown string using pandoc engine."""
    cmd = ["pandoc", "-f", "docx", "-t", "markdown", docx_path]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout
