"""Programmatic fixture generator for 4 sample docx files."""

import os
import docx


def create_sample_docx(
    path: str,
    title: str,
    paragraphs: list,
    table_data=None,
):
    """Creates a sample docx document programmatically."""
    doc = docx.Document()
    doc.add_heading(title, level=1)
    for p in paragraphs:
        doc.add_paragraph(p)
    if table_data:
        table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
        for r_idx, row in enumerate(table_data):
            for c_idx, val in enumerate(row):
                table.rows[r_idx].cells[c_idx].text = str(val)
    doc.save(path)


def generate_all_fixtures():
    """Generates 4 distinct test input files."""
    os.makedirs("test_samples", exist_ok=True)
    create_sample_docx(
        "test_samples/sample1.docx",
        "Document One",
        ["First simple paragraph.", "Second simple paragraph."],
    )
    create_sample_docx(
        "test_samples/sample2.docx",
        "Document Two",
        ["Text with heading and table."],
        table_data=[["Name", "Score"], ["Alice", "95"], ["Bob", "88"]],
    )
    create_sample_docx(
        "test_samples/sample3.docx",
        "Technical Document",
        ["Header test.", "Body test."],
    )
    create_sample_docx(
        "test_samples/sample4.docx",
        "Complex Matrix",
        ["Data summary:"],
        table_data=[["Col1", "Col2"], ["A", "B"], ["C", "D"]],
    )


if __name__ == "__main__":
    generate_all_fixtures()
