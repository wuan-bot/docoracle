## Why

Improve code quality and developer experience by adding comprehensive precommit checks using BasedPyright for strict type checking and Ruff for linting and code formatting (replacing black). This catches issues early, enforces consistent style, and reduces code review friction.

## What Changes

- **NEW**: `.pre-commit-config.yaml` with four staged hooks:
  - `ruff` with auto-fix (expanded rules: E, F, I, N, W, UP, B, C4, SIM)
  - `ruff-format` replacing black for code formatting
  - `basedpyright` in strict mode for type checking
  - `pytest` with `--tb=short` for test execution

- **MODIFY**: `pyproject.toml`:
  - Remove `[tool.black]` configuration (replaced by ruff-format)
  - Remove `mypy` from dev dependencies (replaced by basedpyright)
  - Remove `black` from dev dependencies (replaced by ruff-format)
  - Add `basedpyright>=1.0.0` to dev dependencies
  - Update `[tool.ruff]` select to include B, C4, SIM rule categories
  - Add `[tool.basedpyright]` with strict mode configuration

## Capabilities

### New Capabilities
- `precommit-checks`: Git precommit hooks for automated code quality validation

### Modified Capabilities
- (none)

## Impact

- **Dependencies**: Replaces mypy and black with basedpyright and ruff-format
- **Developer workflow**: Requires `pre-commit install` and initial bulk reformat commit
- **Code style**: Ruff format enforces consistent formatting (line-length: 100)
- **Type safety**: BasedPyright in strict mode catches more type issues than mypy
- **Test feedback**: pytest runs automatically on commit with short traceback output
