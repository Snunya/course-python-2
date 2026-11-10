"""Tests for CLI converter and generated samples."""

import os
from src.cli import main
from tests.make_fixtures import generate_all_fixtures


def test_cli_on_four_samples(tmp_path):
    """Demonstrates CLI conversion across 4 input samples."""
    generate_all_fixtures()
    for i in range(1, 5):
        in_file = f"test_samples/sample{i}.docx"
        out_file = str(tmp_path / f"output{i}.md")
        ret = main(["-i", in_file, "-o", out_file])
        assert ret == 0
        assert os.path.exists(out_file)
        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0
