# nba_analysis

Monorepo for NBA data-analysis projects. Each project answers one question; shared
infrastructure (data fetching/caching, statistics primitives, PDF report
generation) lives in a common library so improvements propagate to every question
instead of being copied by hand.

## Layout

```
nbakit/        # shared library: nba_api fetch+cache, ratings (SRS/RAPM/box-score),
               #   the facts/guards system, and markdown→PDF report generation
cache/         # shared raw-data cache (NBA.com pulls keyed by season + type)
questions/
  home_court/            # NBA home court advantage and its decline
  knicks_2026_historic/  # did the 2025–26 Knicks have a historic playoff run?
  player_rating_overview/# survey and comparison of NBA player-rating systems
  template/              # scaffold cloned to start a new question
```

The two `julia_*` directories in this folder are separate, unrelated Julia repos
and are intentionally not tracked here.

## Working in a question

Each question is self-contained (its own `CLAUDE.md`, data/plots/analysis modules,
a `docs/<project>_findings.md`, and report). Computed numbers are written once as
"facts" and templated into the prose docs, so the findings can't drift from the
analysis. See the per-question `CLAUDE.md` for commands.
