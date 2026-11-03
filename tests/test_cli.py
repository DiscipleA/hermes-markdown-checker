"""Exercise the actual CLI in subprocesses, without third-party dependencies."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args, text="# Demo\n"):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "markdown_checker.py"), *args],
            input=text,
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=ROOT,
            timeout=10,
        )

    def test_clean_stdin_exits_zero_without_output(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((result.stdout, result.stderr), ("", ""))

    def test_reads_one_explicit_utf8_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "résumé.md"
            path.write_text("# Résumé 世界\n\n## Café\n", encoding="utf-8")
            result = self.run_cli(str(path), text="not the file contents")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((result.stdout, result.stderr), ("", ""))

    def test_missing_top_level_heading(self):
        result = self.run_cli(text="Plain paragraph.\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "<stdin>:1: MD001 missing top-level heading (# ...)\n")
        self.assertEqual(result.stderr, "")

    def test_empty_input_is_missing_top_level_heading(self):
        result = self.run_cli(text="")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MD001", result.stdout)

    def test_forward_heading_jump_reports_line_and_levels(self):
        result = self.run_cli(text="# Demo\n\n### Skipped\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "<stdin>:3: MD002 heading level jumps from 1 to 3\n")

    def test_first_deep_heading_is_a_jump(self):
        result = self.run_cli(text="### Deep\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("<stdin>:1: MD001", result.stdout)
        self.assertIn("<stdin>:1: MD002 heading level jumps from 0 to 3", result.stdout)

    def test_trailing_spaces(self):
        result = self.run_cli(text="# Demo\nText.  \n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "<stdin>:2: MD003 trailing whitespace\n")

    def test_trailing_tabs(self):
        result = self.run_cli(text="# Demo\n\t\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("<stdin>:2: MD003 trailing whitespace", result.stdout)

    def test_multiple_findings_are_reported_without_short_circuiting(self):
        result = self.run_cli(text="## Topic \n#### Deep\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count("MD001"), 1)
        self.assertEqual(result.stdout.count("MD002"), 2)
        self.assertEqual(result.stdout.count("MD003"), 1)

    def test_heading_requires_separator_after_hashes(self):
        result = self.run_cli(text="#not-a-heading\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MD001", result.stdout)

    def test_four_space_indented_heading_is_not_atx_heading(self):
        result = self.run_cli(text="    # Code-like text\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MD001", result.stdout)

    def test_seven_hashes_are_not_a_heading(self):
        result = self.run_cli(text="####### Too deep\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MD001", result.stdout)
        self.assertNotIn("MD002", result.stdout)

    def test_dash_explicitly_selects_stdin(self):
        result = self.run_cli("-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_missing_file_is_a_friendly_input_error(self):
        result = self.run_cli("missing-demo-file.md")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_directory_is_a_friendly_input_error(self):
        result = self.run_cli(str(ROOT))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_is_a_friendly_input_error(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "invalid.md"
            path.write_bytes(b"# Title\n\xff")
            result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unicode_filename_in_diagnostic_even_with_ascii_host_encoding(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "résumé-世界.md"
            path.write_text("# Demo\n### Jump\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "markdown_checker.py"), str(path)],
                input="", text=True, encoding="utf-8", capture_output=True,
                env={**os.environ, "PYTHONIOENCODING": "ascii"}, timeout=10,
            )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(f"{path}:2: MD002", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_valid_hierarchy_can_return_to_shallower_headings(self):
        result = self.run_cli(text="# A\n## B\n### C\n## D\n# E\n")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_up_to_three_spaces_before_heading(self):
        result = self.run_cli(text="   # Demo\n  ## Child\n")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_unicode_stdin_bom_crlf_and_no_final_newline(self):
        result = self.run_cli(text="\ufeff# Résumé 世界\r\n\r\n## Café")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_multiple_files(self):
        result = self.run_cli("one.md", "two.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_help(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("UTF-8", result.stdout)


if __name__ == "__main__":
    unittest.main()
