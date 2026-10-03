## 1. Bulk Reformat (One-time Setup)

- [x] 1.1 Run `ruff check --fix src/ tests/` and verify no errors remain
- [x] 1.2 Run `ruff format src/ tests/` and verify all files are formatted
- [x] 1.3 Commit reformatted files with message "chore: bulk reformat with Ruff"

## 2. Create Precommit Configuration

- [x] 2.1 Create `.pre-commit-config.yaml` with ruff, ruff-format, basedpyright, and pytest hooks
- [x] 2.2 Verify file exists and has correct YAML structure

## 3. Update pyproject.toml

- [x] 3.1 Remove `[tool.black]` section and verify it's gone
- [x] 3.2 Remove `black` and `mypy` from dev dependencies in `[project.optional-dependencies]`
- [x] 3.3 Add `basedpyright>=1.0.0` to dev dependencies
- [x] 3.4 Update `[tool.ruff]` select to include `B`, `C4`, `SIM` rule categories
- [x] 3.5 Add `[tool.basedpyright]` section with strict mode and pythonVersion 3.10
- [x] 3.6 Verify `pyproject.toml` is valid TOML and can be parsed

## 4. Install and Validate

- [x] 4.1 Run `pip install pre-commit` and verify installation succeeds
- [x] 4.2 Run `pre-commit install` and verify git hooks are created in `.git/hooks/`
- [x] 4.3 Run `pre-commit run --all-files` and verify all hooks pass
- [x] 4.4 Commit `.pre-commit-config.yaml` and `pyproject.toml` with message "feat: add precommit checks with BasedPyright and Ruff"

## 5. Final Verification

- [x] 5.1 Make a small intentional change (e.g., add a comment) and verify precommit hooks run on commit
- [x] 5.2 Verify ruff check auto-fixes lint issues
- [x] 5.3 Verify ruff format auto-formats code
- [x] 5.4 Verify basedpyright catches type errors (test with intentional type error)
- [x] 5.5 Verify pytest runs and fails commit on test failure
