## Context

Current project uses mypy for type checking and black for formatting, configured in `pyproject.toml`. Ruff is present but with minimal rule set. No precommit hooks are configured. All Python code lives in `src/` and `tests/` directories.

## Goals / Non-Goals

**Goals:**
- Zero-configuration local development setup for code quality
- Consistent code style across all Python files
- Strict type safety with modern type checker (BasedPyright)
- Automatic fixes for linting issues
- Early test feedback before pushing code

**Non-Goals:**
- CI/CD pipeline changes (precommit is local only)
- IDE-specific configuration
- Enforcing commit message format
- Pre-push hooks (only precommit)

## Decisions

### Use pre-commit framework over custom scripts
**Decision:** Adopt the [pre-commit](https://pre-commit.com/) framework.
**Rationale:** Industry standard for Python, manages hook environments automatically, supports repo-wide and local hooks, well-documented, integrates with CI.
**Alternatives considered:**
- Custom Makefile targets: More manual, no automatic environment management
- GitHub Actions only: No local feedback loop
- VS Code extensions: IDE-specific, not enforceable

### Ruff replaces black for formatting
**Decision:** Use `ruff format` instead of black.
**Rationale:** Ruff format is faster (Rust-based), integrates with ruff linting, single tool for both linting and formatting, maintained by same team.
**Alternatives considered:**
- Keep both: Unnecessary duplication
- Keep black: Slower, separate config, two tools to maintain

### BasedPyright over mypy
**Decision:** Use BasedPyright in strict mode instead of mypy.
**Rationale:** BasedPyright is faster, has better Pydantic v2 support, stricter by default, actively maintained, Rust-based for performance.
**Alternatives considered:**
- Keep mypy: Slower, less modern
- pyright: Similar but BasedPyright has better defaults

### Expanded Ruff rule set
**Decision:** Extend Ruff from `E, F, I, N, W, UP` to also include `B, C4, SIM`.
**Rationale:** Bugbear (B) catches common bugs, Comprehensions (C4) improves readability, Simplify (SIM) reduces complexity. All are widely adopted and low-noise.
**Alternatives considered:**
- Keep minimal: Misses many code quality improvements
- All rules: Too noisy, many opinionated rules

### Strict type checking mode
**Decision:** Use `typeCheckingMode = "strict"` for BasedPyright.
**Rationale:** Catches more potential issues, aligns with project's quality goals, BasedPyright's strict mode is well-calibrated.
**Alternatives considered:**
- standard: Less thorough
- basic: Too permissive

### pytest with short traceback
**Decision:** Use `--tb=short` for pytest hook.
**Rationale:** Cleaner output in precommit context, still shows enough info to debug failures.
**Alternatives considered:**
- No tb flag: Verbose output cluttering commit messages
- --tb=line: Too minimal

### Bulk reformat before activating hooks
**Decision:** Run `ruff check --fix` and `ruff format` on all files before first commit with hooks active.
**Rationale:** Prevents the first real commit from being polluted with formatting changes. Makes git history cleaner.
**Alternatives considered:**
- Let precommit handle it: First commit would be huge and noisy

## Risks / Trade-offs

**[Commit latency]** → Precommit hooks add 10-30 seconds to each commit. *Mitigation:* Hooks run in parallel where possible; can use `pre-commit run --all-files` to test locally.

**[Strict type checking breaks existing code]** → BasedPyright strict mode may flag issues mypy didn't. *Mitigation:* Bulk fix before activating; review type errors as real bugs to fix.

**[Ruff expanded rules flag new issues]** → B, C4, SIM rules may catch issues not previously enforced. *Mitigation:* Treat as code quality improvements; fix incrementally or suppress specific rules if justified.

**[Environment dependency]** → Requires basedpyright and ruff installed in dev environment. *Mitigation:* Document in setup instructions; pre-commit framework manages hook environments.

**[Windows compatibility]** → pre-commit works cross-platform; BasedPyright and Ruff are cross-platform. *Mitigation:* Test on Windows during validation.

## Migration Plan

1. **Bulk reformat commit**
   ```bash
   ruff check --fix src/ tests/
   ruff format src/ tests/
   git add -u
   git commit -m "chore: bulk reformat with Ruff"
   ```

2. **Create configuration files**
   - Add `.pre-commit-config.yaml`
   - Update `pyproject.toml` (remove black/mypy, add basedpyright config)
   - Update dev dependencies

3. **Install hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Validate**
   ```bash
   pre-commit run --all-files
   ```

5. **Commit the precommit config**
   ```bash
   git add .pre-commit-config.yaml pyproject.toml
   git commit -m "feat: add precommit checks with BasedPyright and Ruff"
   ```

**Rollback:** Remove `.pre-commit-config.yaml`, revert `pyproject.toml` changes, run `pre-commit uninstall`.

## Open Questions

- Should we add a pre-push hook for additional checks (e.g., test coverage) in the future?
- Should we configure Ruff to fix certain issues automatically that currently require manual fixes?
