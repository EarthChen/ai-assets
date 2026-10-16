
# React Testing

Use React Testing Library (RTL) with the repo's runner (Vitest or Jest). Test what the user sees and does. Behavior that needs a real browser (layout, scrolling, drag-and-drop, clipboard, CSS transitions, iframes) belongs in Playwright or Cypress end-to-end tests: Read [e2e-testing](../../e2e-testing/SKILL.md).

## Queries and Interaction

- Query order: `getByRole(role, { name })`, `getByLabelText`, `getByText`; `getByTestId` only when nothing else fits.
- Use `userEvent.setup()` once per test and `await` every call. `fireEvent` stays out.
- Async content: `await screen.findBy*`; side-effect expectations: `await waitFor(...)`.
- Assert absence with `queryBy*`.

## Network: MSW

Mock the network layer with MSW so components, hooks, and the fetch library behave as in production.

```tsx
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

const server = setupServer(
  http.get("/api/users/:id", ({ params }) => HttpResponse.json({ id: params.id, name: "Alice" })),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// per-test override
server.use(http.get("/api/users/:id", () => new HttpResponse(null, { status: 500 })));
```

## Setup Helpers

Wrap providers once in `test-utils.tsx` as `renderWithProviders(ui)` (QueryClient with a fresh client per call, theme, router) and use it everywhere.

## Hooks and Accessibility

- Test custom hooks with `renderHook` from `@testing-library/react`; wrap state changes in `act` and assert through the public hook API.
- Run `axe` (`vitest-axe` or `jest-axe`) in component tests: `expect(await axe(container)).toHaveNoViolations()`.

## Snapshots

Use snapshots for stable non-visual output (a serializer's string). Assert component output with queries. Cover visual regression with screenshot diffs in Playwright, Cypress, or Percy.

## Anti-Patterns

- Asserting through `container.querySelector`: bypasses accessible queries.
- Asserting on render counts, internal state, props passed to children, or which hooks ran.
- Mocking React hooks (`jest.mock("react", ...)`): refactor the component.
- Mocking child components by default: that tests the parent without its integration.
- Ignoring `act()` warnings: they point to real bugs.
- `setTimeout` plus an assertion: flaky; use `findBy*` or `waitFor`.
