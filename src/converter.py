"""Core module for converting docx format to markdown text."""

import docx


def convert_docx_to_markdown(docx_path: str) -> str:
    """Reads a docx file and transforms content to markdown syntax."""
    doc = docx.Document(docx_path)
    md_lines = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style_name = paragraph.style.name.lower()
        if "heading 1" in style_name:
            md_lines.append(f"# {text}\n")
        elif "heading 2" in style_name:
            md_lines.append(f"## {text}\n")
        elif "heading 3" in style_name:
            md_lines.append(f"### {text}\n")
        else:
            md_lines.append(f"{text}\n")

    for table in doc.tables:
        table_lines = _convert_table(table)
        md_lines.extend(table_lines)

    return "\n".join(md_lines)


def _convert_table(table: docx.table.Table) -> list[str]:
    """Serializes docx table to markdown format."""
    lines = []
    rows = table.rows
    if not rows:
        return lines

    header_cells = [cell.text.strip() for cell in rows[0].cells]
    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")

    for row in rows[1:]:
        cells = [cell.text.strip() for cell in row.cells]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("\n")
    return lines
