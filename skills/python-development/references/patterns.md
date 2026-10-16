# Python Project Conventions

Project layout, typing baseline, and tooling commands. Every command runs through `uv run`; dependencies live in `pyproject.toml`.

## Type Hints

- Target Python 3.12+: built-in generics (`list[str]`, `dict[str, int]`), `X | None`, and PEP 695 syntax (`def first[T](items: list[T]) -> T | None`, `type JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None`).
- Use `Protocol` for structural interfaces instead of ABCs when callers only need a method shape.

## Package Organization

```
myproject/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       ├── models/
│       └── utils/
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_models.py
├── pyproject.toml
└── .gitignore
```

Import order: stdlib, third-party, local. Let ruff sort it: `uv run ruff check --select I --fix .`

`__init__.py` re-exports the public API and declares `__all__`:

```python
from mypackage.models import User, Post
from mypackage.utils import format_name

__all__ = ["User", "Post", "format_name"]
```

## Tooling Commands

Install dev tools: `uv add --dev ruff mypy pytest pytest-cov bandit pip-audit`.

```bash
uv run ruff format .                    # formatter (replaces black)
uv run ruff check --select I --fix .    # import sorting (replaces isort)
uv run ruff check .                     # lint
uv run mypy .                           # type check
uv run pytest --cov=mypackage --cov-report=term-missing
uv run bandit -r src/                   # static security scan
uv run pip-audit                        # dependency CVE scan
```

## pyproject.toml Baseline

```toml
[project]
name = "mypackage"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.0.0"]

[dependency-groups]  # written by `uv add --dev`
dev = ["pytest", "pytest-cov", "ruff", "mypy", "bandit", "pip-audit"]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--strict-markers --cov=mypackage --cov-report=term-missing"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

## Conventions Worth Enforcing

- Log with `logging`, not `print()`; pass lazy args (`logger.error("failed: %s", e)`).
- Raise from the original error (`raise ConfigError(...) from e`); catch specific exceptions.
- Timezone-aware datetimes: `datetime.now(UTC)`.
- Build strings in loops with `"".join(...)`, not `+=`.
