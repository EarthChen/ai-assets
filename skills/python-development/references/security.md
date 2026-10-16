# Python Security

Code-level security constraints for Python services. Scanner commands (`bandit`, `pip-audit`): `patterns.md` → Tooling Commands. This file carries only what to write and what to forbid.

## Rules

### Secrets

- Read secrets from environment variables; never hardcode API keys, tokens, or passwords
- Local development loads from `.env` via `python-dotenv`; the `.env` file itself is git-ignored

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]  # KeyError on missing — fail fast
```

- Production: read from a secret manager (Vault, AWS Secrets Manager) injected as env vars at deploy time

### SQL Injection

- Use the ORM's parameterised API (SQLAlchemy `select(...).where(...)`, Django ORM) or `text("... WHERE id = :id")` + `session.execute(sql, {"id": id})`
- Never `f"SELECT ... {user_input}"` — string interpolation into SQL is injection

```python
# BAD — string interpolation
session.execute(f"SELECT * FROM users WHERE name = '{name}'")

# GOOD — parameterised
session.execute(text("SELECT * FROM users WHERE name = :name"), {"name": name})

# GOOD — ORM
session.execute(select(User).where(User.name == name))
```

### Deserialisation

- `pickle.loads` on untrusted input executes arbitrary code — never use it on data from outside the trust boundary
- For data interchange, use `json` (with type validation via Pydantic or `jsonschema`) or `msgpack`
- If pickle is required for trusted internal sources only, document the trust boundary

### HTML / Output Rendering

- HTML escape before render, or use a templating engine (Jinja2) that auto-escapes by default
- Don't mark strings "safe" (`Markup`, `|safe`) unless they came from a trusted internal source

### Authentication

- Hash passwords with `pwdlib` (argon2) or `argon2-cffi`; `passlib` is unmaintained
- Issue tokens via a vetted library (`pyjwt`); validate `exp`, `iss`, `aud`, `alg` on every request
- Never log credentials, cookies, or full Authorization headers

## Pre-commit

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
```

## Anti-Patterns

- `eval()` or `exec()` on any string derived from user input
- `subprocess.run(user_input, shell=True)` — argument injection vector; pass `shell=False` with argv list
- `requests.get(url)` where `url` is user-controlled without allowlist validation (SSRF)
- Logging the full request body or Authorization header
