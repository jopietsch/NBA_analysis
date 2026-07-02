# CLAUDE.md

[One sentence: what question does this project answer?]

See `project_definition.md` for the full question design (hypothesis, comparison
set, confirmation criteria, objections, done criteria).

The document workflow (naming, facts sourcing, cascade rules) is defined once in
the parent `../CLAUDE.md` (loaded automatically alongside this file). The pipeline
mechanics — module architecture, standard commands, test pattern, and the "adding
a new analysis" order — live in the **`pipeline` skill**; load it before scaffolding
or running the pipeline. Don't restate either here. Use this file only for what is
specific to this project:

- the one-line question above;
- any doc or step that deviates from the standard (an extra companion doc, a
  non-standard report option, a chart that lives outside `docs/`);
- project-specific "when you edit X, also update Y" rules.
