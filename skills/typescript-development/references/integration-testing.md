# Integration Testing (TypeScript Backend)

Principles (boundaries, sociable/solitary, narrow integration, isolation rules, what to mock): Read `../../testing-principles/SKILL.md`. Three-layer assertions, and strict E2E against a running server: Read `../../e2e-testing/references/backend-api.md`. This file carries only the TypeScript stack specifics.

## Stack

- **Runner**: vitest (preferred) or jest; follow the repo's existing setup
- **HTTP**: supertest against the in-process app instance
- **Real database, cache, message broker**: testcontainers-node (Postgres/Redis/…)
- **Outbound third-party HTTP**: nock, or msw when shared with frontend tests

## Real Database via Testcontainers (vitest)

`globalSetup` runs in the main process; test workers do not share its module state. Start the container once there and pass the connection string to tests with `provide` / `inject`.

```typescript
// test/global-setup.ts
import { PostgreSqlContainer, type StartedPostgreSqlContainer } from '@testcontainers/postgresql'
import type { TestProject } from 'vitest/node'

let container: StartedPostgreSqlContainer

export async function setup(project: TestProject) {
  container = await new PostgreSqlContainer('postgres:16').start()
  project.provide('dbUrl', container.getConnectionUri())
  // run the project's migrations against container.getConnectionUri() here
}

export async function teardown() {
  await container.stop()
}

declare module 'vitest' {
  export interface ProvidedContext {
    dbUrl: string
  }
}
```

Register it with `test: { globalSetup: ['./test/global-setup.ts'] }` in `vitest.config.ts`. Per-test isolation lives in a `beforeEach` (transaction rollback or `TRUNCATE ... CASCADE`; policy in testing-principles).

## Integration Test Shape

```typescript
import request from 'supertest'
import { Pool } from 'pg'
import { inject } from 'vitest'
import { createApp } from '../src/app'

const pool = new Pool({ connectionString: inject('dbUrl') })
const api = request(createApp({ pool }))   // build the app against the container database

it('creates an order and persists it', async () => {
  const sku = `it-${crypto.randomUUID().slice(0, 8)}`

  const res = await api.post('/orders').send({ sku, qty: 1 })

  expect(res.status).toBe(201)                                 // layer 1: status
  const persisted = await pool.query('select sku from orders where id = $1', [res.body.id])
  expect(persisted.rows[0]?.sku).toBe(sku)                     // layer 3: persisted
})
```
