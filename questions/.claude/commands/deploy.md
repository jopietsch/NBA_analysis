Publish the generated HTML site (all projects' reports) to GitHub Pages via the repo-root `deploy.sh`.

`deploy.sh` collects every project's `generated/*.html` plus the shared `questions/generated/*.html`, builds an `index.html`, and pushes the whole site to the `gh-pages` branch. It publishes **all** projects at once, not just the one you are currently working in.

**Only deploy from `main`.** The site is the integrated view of every project. A feature branch reflects mid-flight work on one project and may carry stale or missing docs for the others, so publishing from it would push an incomplete site. The command below refuses to run unless the current branch is `main`.

`deploy.sh` copies whatever HTML currently sits in each project's `generated/` directory (those files are gitignored build artifacts, not committed). So before deploying, make sure `main` is current and the reports are freshly built: pull `main`, and if any project's docs changed since its HTML was last generated, run `/regen` in that project first.

Run this single command (it self-guards on the branch, then deploys):

```bash
branch=$(git -C /Users/justin/code/nba_analysis rev-parse --abbrev-ref HEAD)
if [ "$branch" != "main" ]; then
  echo "Refusing to deploy from '$branch': the site publishes all projects, so it must come from main. Switch to main and pull first."
  exit 1
fi
bash /Users/justin/code/nba_analysis/deploy.sh
```

If it refuses because you are not on `main`, tell the user which branch they are on and stop; do not switch branches for them. On success, report the sections and file counts `deploy.sh` printed and note the site will be live at the GitHub Pages URL shortly.
