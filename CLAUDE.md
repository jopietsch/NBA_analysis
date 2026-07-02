# CLAUDE.md — nba_analysis

Repo-wide engineering discipline, applying to every project and package in this repo (`questions/`, `nbakit/`, `julia/`). Project-specific writing rules, the analysis pipeline architecture, and standard commands live in `questions/CLAUDE.md` and each project's own `CLAUDE.md`.

## Working discipline

**Think before coding.** State assumptions explicitly; if uncertain, ask. If multiple interpretations exist, surface them rather than picking silently. If a simpler approach exists, say so and push back when warranted.

**Simplicity first.** Minimum code that solves the problem, nothing speculative: no features beyond what was asked, no abstractions for single-use code, no configurability that wasn't requested, no error handling for impossible scenarios. If 200 lines could be 50, rewrite it. Ask: "would a senior engineer call this overcomplicated?"

**Surgical changes.** Touch only what the request requires; every changed line should trace to it. Don't refactor, reformat, or "improve" adjacent code; match existing style even if you'd do it differently. Remove only the imports/variables your own changes orphaned; mention unrelated dead code rather than deleting it.

**Verify.** Turn the task into a checkable goal ("add validation" → "write tests for invalid inputs, then make them pass"; "fix the bug" → "write a failing test, then make it pass") and loop until it passes. State a brief plan for multi-step work.
