# hermes-markdown-checker

A Python standard-library CLI for a small automation/PR-review demonstration.
It reads stdin or one explicit UTF-8 file and reports three line-based checks.
No installation, network, credentials, or external packages are needed.

## Run

From this folder, with Python 3.10 or newer:

```bash
python -B markdown_checker.py examples/clean.md
python -B markdown_checker.py < examples/clean.md
python -B markdown_checker.py - < examples/clean.md
python -B markdown_checker.py examples/findings.md
```

The clean example produces no output and exits 0. The findings example exits 1:

```text
examples/findings.md:3: MD002 heading level jumps from 1 to 3
examples/findings.md:4: MD003 trailing whitespace
```

Use `--help` for usage. Use `--` before filenames beginning with a dash.
Files and stdin are decoded as UTF-8; an initial UTF-8 BOM is accepted.
Diagnostics are emitted as UTF-8, including Unicode filenames.

## Rules and exit status

| Code | Rule |
| --- | --- |
| MD001 | At least one level-one ATX heading is required anywhere in the document. Missing-heading diagnostics use line 1, even for empty input. |
| MD002 | A heading may deepen by at most one level relative to the previous heading. The initial level is 0; returning to a shallower level is allowed. |
| MD003 | No line may end with an ASCII space or tab, including lines inside code blocks. |

Headings have zero to three leading spaces, one to six hashes, then a space,
tab, or end of line. A bare hash is counted as a heading by this simple checker.
Findings use `source:line: CODE message` on stdout; input and usage errors go
to stderr. Exit 0 means clean, 1 means findings, and 2 means input/usage error.
Nothing is rewritten. Markdown hard-break spaces are also flagged intentionally.

## Test

```bash
python -B -m unittest discover -v
```

The baseline has 22 passing subprocess CLI tests. They exercise all three rules,
line numbers, multiple findings, Unicode stdin and filenames, BOM/CRLF input,
file errors, invalid UTF-8, help, and rejection of multiple files.

## Deliberately seeded presentation issue

**This is a disclosed demo bug, not a complete Markdown parser.** Heading-like
text inside backtick or tilde fenced blocks is currently treated as real
headings. It can produce false heading-level jumps or make a code-only title
satisfy MD001. The baseline intentionally does not claim fenced-code support.

Two separate PR seeds live outside this folder in
`../../scenarios/hermes-markdown-checker/`:

- `bugfix.md` and `test_regression.py`: fix fence handling using a regression-first workflow.
- `enhancement.md`: propose an opt-in maximum-line-length flag (not wrapping).
- `scenario.json`: exact paths, commands, acceptance criteria, and measured counts.
- `verify_scenarios.py`: copy the baseline into a disposable scenario-local folder,
  add the regression there, and save real GREEN/RED logs under `evidence/`.

The regression is intentionally absent from this repository's `tests/` so its
normal baseline stays green. The enhancement is a proposal, not implemented.
Neither seed creates a branch, commit, remote, workflow, or PR.

## Limitations and AI assistance

This is a line-based teaching tool, not CommonMark validation. It does not
recognize Setext headings, nested list/blockquote structure, HTML blocks, escaped
markup, or every indentation context. It reads the whole input into memory.
No recursive scans, automatic edits, configurable rules, or line-length option
are implemented. The three diagnostic codes are local identifiers, not a claim
of compatibility with another Markdown linter's rule numbering.

AI assistance was used to write this demonstration's implementation, tests, and
documentation. The executable test suite and separately reproduced seeded
regression are the verification evidence; the seeded bug is deliberately retained.
