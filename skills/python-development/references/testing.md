# Python Testing Patterns

pytest conventions that go beyond the defaults. Run everything through `uv run pytest`.

## Coverage

Test-first loop: the `tdd` skill. Coverage target: the global 80% rule; critical paths 100%. Measure: `uv run pytest --cov=mypackage --cov-report=term-missing`. Declare `--strict-markers` and the `slow` / `integration` / `unit` markers once in `pyproject.toml` (see `patterns.md` → pyproject.toml Baseline). Select with `uv run pytest -m "not slow"`.

## Async Tests

Use `pytest-asyncio`. In strict mode (the default) async fixtures need `@pytest_asyncio.fixture`; a plain `@pytest.fixture` on an `async def` returns a coroutine.

```python
import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_api_endpoint(async_client):
    response = await async_client.get("/api/data")
    assert response.status_code == 200
```

Mock async callables with `patch(...)` (auto-detects `async def`) and assert with `assert_awaited_once()`.

## Mocking

- Use `autospec=True` so a mock fails when the real signature changes.
- Patch where the name is looked up (`mypackage.service.external_call`), not where it is defined.

## Integration Testing

Principles (boundaries, sociable/solitary, narrow integration, isolation rules): Read `../../testing-principles/SKILL.md`. This section carries only the Python stack specifics.

### Real Database via Testcontainers

```python
import pytest
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()

@pytest.fixture
def db_session(postgres_url):
    engine = create_engine(postgres_url)
    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    yield session
    session.rollback()   # isolation: roll back instead of cleaning up rows
    session.close()
```

### API + Database Together

FastAPI: `TestClient(app)` (sync) or `httpx.AsyncClient` with `ASGITransport` (async). Flask/Quart: `app.test_client()`. FastAPI override rules: `fastapi.md` → Testing.

```python
@pytest.fixture
def client(db_session):
    app = create_app(testing=True)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.integration   # marker declared in pyproject.toml
def test_create_user_persists(client, db_session):
    resp = client.post("/api/users", json={"name": "Alice", "email": "alice@example.com"})
    assert resp.status_code == 201

    # Persisted side effect — a status code alone proves nothing
    found = db_session.query(User).filter_by(email="alice@example.com").first()
    assert found is not None
```

### What to Mock

Policy: Read `../../testing-principles/SKILL.md` (What to Mock). Python tools: testcontainers for the real database, cache, and message broker; `respx` (httpx) and `responses` (requests) for third-party HTTP boundaries.
