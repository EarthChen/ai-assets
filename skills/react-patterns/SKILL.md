---
name: react-patterns
description: React component architecture patterns — container/presentational split, state location, RSC boundary, Suspense, forms, data fetching, lists, composition, compound components, portals — plus React hooks rules. Use when designing or reviewing React component structure and hook usage.
metadata:
  origin: ECC
---

# React Patterns

> For hook-specific rules see [react-hooks.md](./react-hooks.md).

## When to Use

- Designing or reviewing React component architecture (container vs presentational split, composition, compound components, portals)
- Deciding where state lives (`useState` / lift / Context / external store / server-state)
- Drawing the Server/Client Component boundary in Next.js App Router (RSC)
- Wrapping data in Suspense + Error Boundaries; choosing a form strategy (uncontrolled vs controlled vs library)
- Selecting a data-fetching strategy; choosing list keys; reviewing React hooks usage

## Container / Presentational Split

Container components own data fetching, state, and side effects. Presentational components receive props and render — no service calls, no hooks beyond local UI state.

```tsx
// Container — owns data
export function UserPage({ userId }: { userId: string }) {
  const { data: user, isLoading } = useUser(userId);
  if (isLoading) return <Spinner />;
  if (!user) return <NotFound />;
  return <UserCard user={user} onSelect={handleSelect} />;
}

// Presentational — pure
export function UserCard({ user, onSelect }: { user: User; onSelect: (id: string) => void }) {
  return <button onClick={() => onSelect(user.id)}>{user.name}</button>;
}
```

## State Location Decision Tree

1. Used by one component → `useState` inside it
2. Used by parent + a few children → lift to nearest common ancestor, pass via props
3. Used across distant branches → React Context **for low-frequency reads only** (theme, auth, locale)
4. High-frequency updates shared across the tree → external store (Zustand, Jotai, Redux Toolkit)
5. Server-derived data → server-state library (TanStack Query, SWR, RSC fetch) — not application state

Context misused for frequently changing values causes every consumer to re-render on every update.

## Server / Client Component Boundary (RSC, Next.js App Router)

- Server Components are the default — they run on the server, do not ship to the client, and can `await` directly
- Client Components opt in with `"use client"` at the top of the file
- Data flows down: a Server Component can render a Client Component and pass serializable props
- A Client Component cannot import a Server Component, but it can receive one via `children` or named slots

```tsx
// Server (default)
export default async function Page() {
  const user = await fetchUser();
  return <UserClient user={user} />;
}

// Client
"use client";
export function UserClient({ user }: { user: User }) {
  const [tab, setTab] = useState("profile");
  return <Tabs value={tab} onChange={setTab}>{user.name}</Tabs>;
}
```

- Never import `"server-only"` packages (DB clients, secrets) from a Client Component file — wrap them in a Server Component or Server Action
- Mark sensitive modules with `import "server-only"` so the bundler errors if a client file imports them

## Suspense + Error Boundaries

Every Suspense boundary needs an Error Boundary above it. The pair handles both states.

```tsx
<ErrorBoundary fallback={<ErrorView />}>
  <Suspense fallback={<Skeleton />}>
    <UserDetails id={id} />
  </Suspense>
</ErrorBoundary>
```

- Place Suspense boundaries close to where data is needed, not at the route root
- Multiple narrower boundaries reveal loaded content progressively
- Error Boundary must be a Class Component (React 19 has no functional equivalent yet) OR use a library wrapper such as `react-error-boundary`

## Forms

### Uncontrolled (React 19 + form actions)

Prefer uncontrolled inputs with form actions when the form has a clear submit step. The browser owns the value; React reads it via `FormData` on submit.

```tsx
async function action(formData: FormData) {
  "use server";
  await saveUser({ name: String(formData.get("name")) });
}

export function UserForm() {
  return (
    <form action={action}>
      <input name="name" required />
      <button type="submit">Save</button>
    </form>
  );
}
```

### Controlled

Use controlled inputs when the value drives other UI, requires real-time validation, or formatting.

```tsx
const [email, setEmail] = useState("");
return <input value={email} onChange={(e) => setEmail(e.target.value)} />;
```

### Form Libraries

For complex forms (multi-step, dynamic field arrays, cross-field validation), use a library:

- React Hook Form — minimal re-renders, uncontrolled-first
- TanStack Form — typed, framework-agnostic
- Final Form — when subscription-based re-renders matter

## Data Fetching

| Strategy | When |
| --- | --- |
| RSC fetch (`await` in Server Component) | Per-request data in Next.js App Router, no client-side cache needed |
| TanStack Query | Client-side cache, mutations, optimistic updates, polling |
| SWR | Lightweight cache + revalidation, simpler than TanStack Query |
| `fetch` in `useEffect` | Avoid — race conditions, no cache, no retry. Only acceptable for one-off fire-and-forget |

Never fetch in a `useEffect` when a real cache library is available — they handle deduping, cache invalidation, error retry, and Suspense integration.

## Lists and Keys

- `key` must be stable across renders — never `index` for any list that can reorder, insert, or delete
- `key` must be unique among siblings, not globally
- A reordered list with index keys causes state in child components to attach to the wrong row

## Composition over Inheritance

- Pass `children` for slot-style composition
- Pass render-prop functions for parameterized rendering
- Pass component types for plug-in points: `renderItem={UserRow}`
- Never extend a component class to specialize behavior

## Compound Components

For related controls (Tabs, Accordion, Menu), use compound components sharing state via Context:

```tsx
<Tabs defaultValue="profile">
  <Tabs.List>
    <Tabs.Trigger value="profile">Profile</Tabs.Trigger>
    <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Panel value="profile"><ProfileForm /></Tabs.Panel>
  <Tabs.Panel value="settings"><SettingsForm /></Tabs.Panel>
</Tabs>
```

## Portals

Use `createPortal` for modals, tooltips, toast containers — anything that must escape the parent's `overflow: hidden` or `z-index` stacking context. Render to a stable DOM node mounted in `index.html`.

## Refs and Forwarding (React 19+)

React 19 lets function components accept `ref` as a regular prop — `forwardRef` is no longer required.

```tsx
export function Input({ ref, ...rest }: { ref?: React.Ref<HTMLInputElement> } & InputProps) {
  return <input ref={ref} {...rest} />;
}
```

Older codebases on React 18 still need `forwardRef`.

## Out of Scope (Pointer Sections)

### Next.js (App Router)

- Server Actions, Route Handlers, Middleware, Parallel/Intercepted Routes, streaming Metadata
- Treated as a separate framework concern — when adding deep Next-specific patterns, propose a dedicated `rules/nextjs/` track
- For now follow Next.js official docs for App Router specifics

### React Native

- Platform-specific imports (`Platform.OS`, `.ios.tsx` / `.android.tsx`), `StyleSheet`, navigation libraries (React Navigation, Expo Router)
- Treated as a separate track — `rules/react-native/` is not yet present
- React core hooks/patterns from this file still apply

## Hooks

> This file covers **React hooks** (`useState`, `useEffect`, `useMemo`, `useCallback`, custom hooks) — NOT the Claude Code `hooks/` runtime system. Naming matches the per-language convention `rules/<lang>/hooks.md` used across this repo.

### Rules of Hooks

Enforce `eslint-plugin-react-hooks` with `react-hooks/rules-of-hooks` set to error.

1. Hooks only at the top level of a function component or another hook
2. Never in loops, conditionals, nested functions, or after early returns
3. Always called in the same order on every render
4. Only inside React function components or custom hooks (functions starting with `use`)

```tsx
// WRONG: conditional hook
function Foo({ enabled }: { enabled: boolean }) {
  if (enabled) {
    const [x, setX] = useState(0); // rule violation
  }
}

// CORRECT: hook unconditional, condition inside
function Foo({ enabled }: { enabled: boolean }) {
  const [x, setX] = useState(0);
  if (!enabled) return null;
  return <span>{x}</span>;
}
```

### `useEffect` — When NOT to Use

`useEffect` is for synchronizing with external systems (subscriptions, browser APIs, third-party libraries). It is **not** the right tool for:

- Derived state — compute it during render
- Transforming data for rendering — compute it during render
- Resetting state when a prop changes — use a `key` on the parent or derive from props
- Notifying parents of state changes — call the callback in the event handler
- Initializing app-level singletons — call the function module-side or in `main.tsx`

```tsx
// WRONG: effect for derived state
const [fullName, setFullName] = useState("");
useEffect(() => {
  setFullName(`${first} ${last}`);
}, [first, last]);

// CORRECT: derive during render
const fullName = `${first} ${last}`;
```

### Dependency Arrays

- Always include every reactive value referenced inside the effect/callback
- Enable `react-hooks/exhaustive-deps` lint rule — never silence it without a comment explaining why
- If the dep array grows unwieldy, the effect is doing too much — split it
- Stable identity for functions passed in deps: wrap in `useCallback` only when the function is itself a dependency of another hook or passed to a memoized child

### Cleanup

Every subscription, interval, listener, or in-flight request must clean up.

```tsx
useEffect(() => {
  const controller = new AbortController();
  fetch(url, { signal: controller.signal }).then(handleResponse);
  return () => controller.abort();
}, [url]);
```

```tsx
useEffect(() => {
  const id = setInterval(tick, 1000);
  return () => clearInterval(id);
}, []);
```

Missing cleanup = race conditions when deps change, memory leaks on unmount.

### `useMemo` and `useCallback` — When Worth It

Default position: **do not memoize**. Add `useMemo` / `useCallback` only when:

1. The value is passed to a `React.memo`-wrapped child as a prop, and identity matters
2. The value is a dependency of another `useEffect` / `useMemo` / `useCallback`
3. The computation is measurably expensive (profile before assuming)

Premature memoization adds noise, hides bugs, and can be slower than the recompute it replaces.

### Custom Hooks

Extract a custom hook when:

- The same hook sequence (state + effect + computed) appears in 2+ components
- The logic has a clear, nameable purpose (`useDebounce`, `useOnClickOutside`, `useLocalStorage`)
- You want to test the logic independently of any component

Do NOT extract when:

- It would have a single caller — inline it
- The "hook" is just `useState` with a different name — adds indirection, no value

```tsx
export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
```

### `useState` Patterns

- Initial state from prop only at mount: pass a function `useState(() => computeInitial(prop))` when computation is expensive
- Functional updater when the new state depends on the old: `setCount(c => c + 1)` — never `setCount(count + 1)` inside async or batched contexts
- Group related state into one object only when they always change together; otherwise split into multiple `useState` calls
- Use `useReducer` once state transitions are conditional on the previous state or there are 3+ related values

### `useRef` Patterns

- DOM refs for imperative APIs (focus, scroll, third-party libs)
- Mutable container that does not trigger re-render (timer ids, previous values, "is mounted" flags)
- Never read or write `ref.current` during render — only inside effects or event handlers
- `useImperativeHandle` only when exposing a child API to a parent ref — last-resort escape hatch

### `useSyncExternalStore`

Use this hook to subscribe to any external store (browser API, third-party state lib, custom event emitter). It is the supported way to make external state safe with concurrent rendering.

```tsx
const isOnline = useSyncExternalStore(
  (cb) => {
    window.addEventListener("online", cb);
    window.addEventListener("offline", cb);
    return () => {
      window.removeEventListener("online", cb);
      window.removeEventListener("offline", cb);
    };
  },
  () => navigator.onLine,
  () => true,
);
```

### React 19 Additions

- `use()` — unwrap promises and contexts inline; usable conditionally (only hook with that property)
- `useFormStatus()` / `useFormState()` (or `useActionState`) — form submission state without prop drilling
- `useOptimistic()` — optimistic UI updates while a server action is pending
- `useTransition()` — mark non-urgent state updates so urgent ones stay responsive

When the project targets React 19+, prefer these over hand-rolled equivalents.

### Stale Closure Trap

Async handlers and intervals capture the values from the render where they were created. Fix by:

1. Using the functional updater form of `setState`
2. Putting the changing value in the dep array of `useEffect` and rebuilding the handler
3. Reading from a ref that is kept in sync

### Lint Configuration

Required rules:

```json
{
  "rules": {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

Treat `exhaustive-deps` warnings as errors in CI for new code.
