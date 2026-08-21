# Integration Testing (TypeScript Backend)

Principles (boundaries, sociable/solitary, narrow integration, isolation rules): `~/.agents/skills/testing-principles/SKILL.md`. Three-layer assertions for API tests: `~/.agents/skills/e2e-testing/references/backend-api.md`. This file carries only the TypeScript stack specifics.

## Stack

- **Runner**: vitest (preferred) or jest — follow the repo's existing setup
- **HTTP**: supertest against the app instance
- **Real database**: testcontainers-node (Postgres/Redis/…)
- **External HTTP mock**: nock or msw — never hit real third-party APIs

## Real Database via Testcontainers

```typescript
// testcontainers.setup.ts
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql'

export let container: StartedPostgreSqlContainer
export let pool: Pool

export async function setupDatabase() {
  container = await new PostgreSqlContainer('postgres:16').start()
  pool = new Pool({ connectionString: container.getConnectionUri() })
  await migrate(pool)   // run the project's migrations against the container
}

export async function teardownDatabase() {
  await pool.end()
  await container.stop()
}
```

## Integration Test Shape

```typescript
import request from 'supertest'
import { app } from '../src/app'
import { pool } from './testcontainers.setup'

// supertest imports the app IN-PROCESS — convenient, but strictly speaking
// that is integration territory. For strict E2E, point at a running server:
// see ~/.agents/skills/e2e-testing/references/backend-api.md
const api = () => request(app)

it('creates an order and persists it', async () => {
  const sku = `e2e-${crypto.randomUUID().slice(0, 8)}`

  const res = await api()
    .post('/orders')
    .set('Authorization', `Bearer ${process.env.E2E_TOKEN}`)  // real auth flow in a fixture
    .send({ sku, qty: 1 })

  expect(res.status).toBe(201)                                 // layer 1: status

  const persisted = await pool.query('select sku from orders where id = $1', [res.body.id])
  expect(persisted.rows[0]?.sku).toBe(sku)                     // layer 3: persisted
})
```

## What to Mock

- **Real**: database, cache, message broker — all via testcontainers
- **Mocked**: third-party HTTP boundaries — nock intercepts outbound calls; msw when shared with frontend tests
- **Never mock**: the code under test, the auth layer

## Isolation

- Default: transaction rollback; fall back to per-test truncation (`TRUNCATE ... CASCADE` in `beforeEach`) when the code under test manages its own transactions or commits from other threads
- vitest wiring: `globalSetup` starts the container once; per-test isolation in a `beforeEach`
