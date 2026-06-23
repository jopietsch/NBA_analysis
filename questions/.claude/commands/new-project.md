Create a new analysis project by copying `questions/template/` and substituting `PROJECT` with the given name.

`$ARGUMENTS` is the project name — a lowercase, underscore-separated slug (e.g. `celtics_dynasty_2026`). If it is empty, ask the user for the name before proceeding.

---

## Steps

**1. Validate the name.**

- The name must be a non-empty lowercase slug (letters, digits, underscores only). If it contains spaces or uppercase, convert it and confirm with the user before continuing.
- Check that `questions/<name>/` does not already exist. If it does, stop and tell the user.

**2. Copy the template.**

Run from the repo root (`/Users/justin/code/nba_analysis`):

```bash
cp -r questions/template questions/<name>
```

**3. Rename files that contain `PROJECT` in their name.**

```bash
cd questions/<name>

# docs/
for f in docs/PROJECT_*; do
  mv "$f" "${f/PROJECT/<name>}"
done

# tests/
for f in tests/test_PROJECT*; do
  mv "$f" "${f/PROJECT/<name>}"
done
```

**4. Substitute `PROJECT` with the actual name in every file's content.**

```bash
find questions/<name> -type f \
  ! -path '*/.git/*' \
  -exec sed -i '' 's/PROJECT/<name>/g' {} +
```

**5. Verify.**

```bash
# Should print nothing — no stale PROJECT references remain
grep -r 'PROJECT' questions/<name> --include='*.py' --include='*.md' --include='*.ini' --include='*.txt'

# Show what was created
find questions/<name> -type f | sort
```

If `grep` finds any remaining `PROJECT` strings, fix them before continuing.

**6. Stage the new directory.**

```bash
git -C /Users/justin/code/nba_analysis add questions/<name>/
git -C /Users/justin/code/nba_analysis status
```

Do NOT commit yet — the user needs to fill out `project_definition.md` and the `CLAUDE.md` description first.

**7. Report and prompt next steps.**

Tell the user what was created. Then say:

> Before writing any code, fill out `project_definition.md` (question, hypothesis, comparison set, confirmation/refutation criteria, done checklist) and update the one-line description at the top of `CLAUDE.md`. When both are done, you're ready to start on `<name>_data.py`.
