"""Command line interface for document transformation."""

import argparse
import sys
from src.converter import convert_docx_to_markdown


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="Transform docx files into markdown documents."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the input docx file",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to save the generated markdown file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for CLI utility."""
    args = parse_arguments(argv if argv is not None else sys.argv[1:])
    try:
        markdown_result = convert_docx_to_markdown(args.input)
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(markdown_result)
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
