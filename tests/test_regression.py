"""Copy into the repo's tests/ to demonstrate the intentionally seeded fence bug."""

from pathlib import Path
import subprocess
import sys
import unittest

from markdown_checker import check_markdown


class FenceRegressionTests(unittest.TestCase):
    def test_backtick_fenced_headings_are_ignored(self):
        self.assertEqual(check_markdown("# Demo\n```markdown\n#### Fake\n```\n## Real\n"), [])

    def test_tilde_fenced_headings_are_ignored(self):
        self.assertEqual(check_markdown("# Demo\n~~~markdown\n#### Fake\n~~~\n## Real\n"), [])

    def test_fenced_h1_does_not_satisfy_required_heading(self):
        findings = check_markdown("```\n# Fake title\n```\nParagraph.\n")
        self.assertEqual([(f.line, f.code) for f in findings], [(1, "MD001")])

    def test_other_fence_character_cannot_close(self):
        for opener, other in (("```", "~~~"), ("~~~", "```")):
            with self.subTest(opener=opener):
                text = f"# Demo\n{opener}\n{other}\n#### Still code\n{opener}\n## Real\n"
                self.assertEqual(check_markdown(text), [])

    def test_shorter_fence_cannot_close(self):
        for char in ("`", "~"):
            with self.subTest(char=char):
                text = f"# Demo\n{char * 4}\n{char * 3}\n#### Still code\n{char * 4}\n## Real\n"
                self.assertEqual(check_markdown(text), [])

    def test_longer_matching_fence_closes(self):
        for char in ("`", "~"):
            with self.subTest(char=char):
                text = f"# Demo\n{char * 3}\n#### Code\n{char * 5}\n### Real jump\n"
                self.assertEqual([(f.line, f.code) for f in check_markdown(text)], [(5, "MD002")])

    def test_closing_fence_cannot_have_non_whitespace_suffix(self):
        text = "# Demo\n```\n```not-a-close\n#### Still code\n```\n## Real\n"
        self.assertEqual(check_markdown(text), [])

    def test_indented_fences_allow_up_to_three_spaces(self):
        text = "# Demo\n   ~~~~python\n#### Code\n  ~~~~~ \n## Real\n"
        self.assertEqual(check_markdown(text), [])

    def test_unclosed_fence_ignores_headings_until_eof(self):
        self.assertEqual(check_markdown("# Demo\n```\n#### Still code\n"), [])

    def test_normal_heading_jumps_still_reported(self):
        self.assertEqual([(f.line, f.code) for f in check_markdown("# Demo\n### Jump\n")], [(2, "MD002")])

    def test_trailing_whitespace_inside_fence_still_reported(self):
        text = "# Demo\n```\ncode \n```\n"
        self.assertEqual([(f.line, f.code) for f in check_markdown(text)], [(3, "MD003")])

    def test_cli_ignores_fenced_heading(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-B", str(root / "markdown_checker.py")],
            input="# Demo\n```\n#### Code\n```\n## Real\n",
            text=True, encoding="utf-8", capture_output=True, cwd=root, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
