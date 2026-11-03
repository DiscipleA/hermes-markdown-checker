# Add an opt-in --max-line-length checker

AI-assisted demonstration planning artifact. No feature implementation is included.

## Acceptance criteria
- [ ] Omitting the option preserves current behavior; require a positive integer.
- [ ] Report MD004 for lines longer than N, count Unicode code points without line terminators, and allow exactly N.
- [ ] Include fenced code, preserve existing findings, and never wrap or modify files.

## Test plan
Add behavior tests first, observe failure, implement only the approved enhancement, and rerun the full baseline suite.

## Status
Draft planning only. Waiting for owner authorization; the maintenance job must leave this branch unchanged.
