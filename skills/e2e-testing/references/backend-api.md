# Backend / API E2E Patterns

Reference for backend E2E testing: testing a service through its public HTTP interface against a running environment with real dependencies. Consumed by the `e2e-testing` skill (backend branch) and the `e2e-runner` agent.

Boundary: mocked dependencies make the suite an integration test, not E2E. Load/performance testing is a separate discipline. Full testing ladder and cross-stack principles: `~/.agents/skills/testing-principles/SKILL.md`.

## Tool Selection by Stack

| Stack | Harness | Note |
| --- | --- | --- |
| Node/TS | supertest, or fetch/axios against a running server | supertest imports the app in-process — integration territory for strict E2E |
| Python | pytest + httpx | session-scoped client fixture |
| Java / Kotlin | REST Assured | identical on both JVM languages |
| Go | `net/http/httptest` or resty + testify | `httptest` serves in-process; strict E2E hits the running addr |
| Rust | reqwest + `#[tokio::test]` | |
| C#/.NET | HttpClient + xUnit | `WebApplicationFactory` is in-process — strict E2E hits the running host |
| Ruby | Faraday or Rack::Test + rspec/minitest | Rack::Test is in-process |
| PHP | PHPUnit + Guzzle or Symfony HttpClient | |

The worked examples below (Python / TypeScript / Java) illustrate the three-layer pattern — it transfers unchanged to every stack in the table: same three layers, same auth/isolation discipline, only the client syntax differs.

## The Three-Layer Assertion

Every E2E test asserts three layers — a `200` alone proves little:

1. **Status code** — the HTTP outcome
2. **Response schema** — the shape matches the contract (OpenAPI spec when present)
3. **Persisted side effect** — the data actually landed: follow-up GET or direct DB query

### Python (pytest + httpx)

```python
import uuid
import httpx
import pytest

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session")
def api_token() -> str:
    # Real login against the running service — never mock the auth layer
    resp = httpx.post(f"{BASE_URL}/auth/login", json={
        "username": "e2e-user", "password": "e2e-password",
    })
    assert resp.status_code == 200
    return resp.json()["token"]

@pytest.fixture
def client(api_token) -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {api_token}"},
        timeout=10,
    )

def test_create_order(client: httpx.Client):
    # Unique suffix → parallel runs never collide
    sku = f"e2e-{uuid.uuid4().hex[:8]}"

    resp = client.post("/orders", json={"sku": sku, "qty": 1})
    assert resp.status_code == 201                    # layer 1: status
    assert resp.json()["status"] == "pending"          # layer 2: schema/shape

    got = client.get(f"/orders/{resp.json()['id']}")
    assert got.status_code == 200                      # layer 3: persisted
    assert got.json()["sku"] == sku
```

Schema validation against an OpenAPI spec (Python): `openapi-core` validates responses against `openapi.yaml` — wire it into a fixture or assert per-endpoint.

### TypeScript (supertest)

```typescript
import request from 'supertest'
import { db } from '../src/db'

// supertest imports the app IN-PROCESS — convenient, but strictly speaking
// that is integration territory. For strict E2E, point at a running server:
const BASE = process.env.BASE_URL ?? 'http://localhost:3000'
const api = () => request(BASE)

it('creates an order', async () => {
  const sku = `e2e-${crypto.randomUUID().slice(0, 8)}`

  const res = await api()
    .post('/orders')
    .set('Authorization', `Bearer ${process.env.E2E_TOKEN}`)  // real token
    .send({ sku, qty: 1 })

  expect(res.status).toBe(201)                               // layer 1

  const persisted = await db.order.findUnique({ where: { id: res.body.id } })
  expect(persisted?.sku).toBe(sku)                           // layer 3
})
```

Schema validation against an OpenAPI spec (Node): `ajv` compiled from the spec's JSON Schema, or `express-openapi-validator` on the server side plus client-side `ajv` asserts.

### Java (REST Assured)

```java
given()
    .auth().oauth2(token)                    // real token from a setup fixture
    .body(new Order(sku, 1))
.when()
    .post("/orders")
.then()
    .statusCode(201)                         // layer 1
    .body("status", equalTo("pending"));     // layer 2

given().when().get("/orders/{id}", id)
    .then().statusCode(200)                  // layer 3: persisted
    .body("sku", equalTo(sku));
```

## Environment Management

- **Real dependencies**: docker-compose (or Testcontainers) for the DB and downstreams the service actually uses
- **Readiness**: poll the health endpoint until ready — never a fixed sleep:

```bash
until curl -sf http://localhost:8000/health; do sleep 0.5; done
```

- **Auth fixture**: one session-scoped real login; per-test tokens only when tests must not share auth state
- **Data isolation**: seed/cleanup fixtures per test; unique-ID suffixes on all test data so parallel workers never collide
- **Async work**: poll until a deadline (`GET /jobs/{id}` until `status == "done"`), never `sleep(30)`

## Anti-Patterns

- Mocking the DB or downstream services → integration test, not E2E
- Mocking the auth layer → auth bugs ship to production
- Asserting only the status code → a `200` with garbage data proves nothing
- Fixed sleeps for async work → the #1 flake source; poll conditions instead
- Shared mutable test data across tests → order-dependent failures
