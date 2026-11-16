# Contributing

These rules apply to every change in this repository. It is a one-person
project, but the rules stay the same as in a team: they keep `main` working
and make every change traceable.

## Branching strategy: GitHub Flow

`main` is **always working and deployable**. Nobody pushes directly to `main`;
it is protected by a branch protection rule.

1. Create a short-lived branch from `main` for one task.
2. Commit, push and open a **pull request**.
3. Review your own change in the pull request (checklist below) and write the
   result into the pull request description.
4. Wait until the CI pipeline is **green** (Lint, Test, Build image).
5. Merge into `main` and delete the branch.

```bash
git switch main
git pull
git switch -c feature/add-ci-pipeline
# ... work and commit ...
git push -u origin feature/add-ci-pipeline
# open the pull request on GitHub and fill in the description
```

### Branch names

Pattern: `<type>/<short-description>`, in English, lower case, words separated
by hyphens.

| Type | Purpose | Example |
| --- | --- | --- |
| `feature/` | new functionality or pipeline step | `feature/add-ci-pipeline` |
| `fix/` | bug fix | `fix/ready-returns-500` |
| `chore/` | maintenance, tools, dependencies | `chore/update-ruff` |
| `docs/` | documentation only | `docs/add-deployment-runbook` |

## Commit messages

From the CI pipeline on, this project uses
[Conventional Commits](https://www.conventionalcommits.org/): in English,
imperative mood, no full stop at the end.

```
<type>: <short summary>

<optional body: why the change was made>
```

Allowed types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

Examples:

```
feat: add summary endpoint
fix: return 404 when an expense does not exist
test: add tests for the postgres repository
ci: add github actions pipeline
docs: add contributing guide
```

Small commits that each do one thing are better than one big commit.

## Self-review in the pull request

In a team, another person would review the pull request. In this project I do
it myself: I read my own diff **on GitHub** once more before merging. Every
pull request description answers:

- **What** does this pull request change?
- **Why** is the change needed?
- Is the CI pipeline green?
- Are there tests for the change, or why are none needed?
- Is the documentation updated, if needed?
- Is anything deliberately left open?

The template in `.github/pull_request_template.md` is filled in automatically
when a pull request is opened.

## Check locally before every push

```bash
make lint   # ruff check and ruff format --check
make cov    # tests with coverage report, must be at least 80 %
```

This avoids red pipelines and extra work in the pull request.

## Further rules

- No `--force` push to `main`.
- Never commit secrets (passwords, tokens, keys). Configuration comes from
  environment variables; `.env` is in `.gitignore`.
- Delete the branch after the merge.
