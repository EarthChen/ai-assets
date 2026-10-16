# FastAPI Conventions

FastAPI structure, async patterns, DI, schemas, security, and testing. This file carries only what is specific to FastAPI.

## Rules

### Application Factory

- Build the app inside `create_app()`; do not instantiate `FastAPI()` at module import time
- Wire routers, middleware, exception handlers, and `lifespan` inside `create_app()`
- Settings loaded once at startup and injected via `Depends` — not read inside route handlers

```python
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="markets", version="1.0.0")
    app.include_router(markets_router, prefix="/api/markets")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins)
    return app

app = create_app()  # for `uvicorn app:app`
```

### Routers Stay Thin

- Endpoints dispatch to services; no business logic, no DB session creation, no long-lived clients
- Persistence lives in repositories or CRUD modules
- `SessionLocal()`, `httpx.Client()`, `boto3.client(...)` constructed in route handlers leak across requests and break concurrency

### Async Discipline

- `async def` for endpoints performing I/O
- From async routes: only call async DB drivers (`AsyncSession`) and async HTTP clients (`httpx.AsyncClient`)
- Never call `requests`, sync SQLAlchemy sessions, blocking file I/O, or `time.sleep` from async routes

```python
# BAD — sync HTTP from async route
@router.get("/external")
async def fetch():
    return requests.get("https://api.example.com").json()  # blocks event loop

# GOOD
@router.get("/external")
async def fetch():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.example.com")
        return r.json()
```

### Dependency Injection

- `Depends(get_db)`, `Depends(get_current_user)` etc. for per-request resources
- DB sessions and auth checkouts belong in dependencies, never constructed inside handlers

```python
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
```

### Schemas

- Separate `Create`, `Update`, and `Response` schemas — never reuse one Pydantic model for all three
- `Response` schemas must not include password, password hash, access token, refresh token, or internal auth state
- Declare `response_model` on every endpoint that returns application data; FastAPI filters out undeclared fields
- Use field constraints (`Field(min_length=...)`, `conint(gt=0)`) over hand-written validation when Pydantic can express the rule

## Security

- CORS origins are environment-specific; never `["*"]` in production, and never wildcard origins with `allow_credentials=True`
- Rate-limit auth and write-heavy endpoints (slowapi or upstream gateway)
- JWT validation, secrets, and log redaction: `security.md`

## Testing

- Override the exact dependency used by `Depends` via `app.dependency_overrides[get_db] = lambda: test_db`
- Clear `app.dependency_overrides` in test teardown — overrides leak across tests
- Use `httpx.AsyncClient` with `ASGITransport(app=app)` for async apps; `TestClient` works but is sync

Fixture example: `testing.md` → API + Database Together.
