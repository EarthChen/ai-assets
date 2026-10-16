
# React Coding Style

## File Extensions

- `.tsx` for any file containing JSX, even one-liner snippets
- `.ts` for pure logic, custom hooks without JSX, type definitions, utilities
- `.test.tsx` / `.test.ts` mirroring the source file
- Use `.jsx` only when the project intentionally avoids TypeScript — flag every new untyped React file in review

## Naming

- Components: `PascalCase` for both the symbol and the file (`UserCard.tsx`, default export `UserCard`)
- Custom hooks: `useCamelCase` for the symbol, kebab-case for the file when the project convention is kebab-case (`use-debounce.ts` exports `useDebounce`)
- Context: `<Domain>Context` symbol, `<Domain>Provider` provider component, `use<Domain>` consumer hook
- Event handlers: `handleClick`, `handleSubmit` inside the component; the prop that receives it is `onClick`, `onSubmit`
- Boolean props: `isLoading`, `hasError`, `canSubmit` — never `loading` or `error` alone for booleans

## Component Shape

```tsx
type Props = {
  user: User;
  onSelect: (id: string) => void;
};

export function UserCard({ user, onSelect }: Props) {
  return (
    <button type="button" onClick={() => onSelect(user.id)}>
      {user.name}
    </button>
  );
}
```

- Prefer `type Props = {}` for closed component prop shapes
- Use `interface` only when the prop type is extended via declaration merging or exported as a public API extension point
- Always destructure props in the parameter list — no `props.user` access inside the body
- Type the return implicitly through JSX (`function Foo(): React.JSX.Element` only when the function returns conditionally and the union confuses inference)

## JSX

- Self-close tags with no children: `<img />`, `<UserCard user={u} />`
- Use fragments `<>...</>` over wrapper `<div>` when no DOM element is needed
- Conditional rendering: `{condition && <Foo />}` for booleans, ternary for either/or, early return for guard clauses
- Never put logic inline in JSX when it reads as multi-line — extract to a const above the return or a function

```tsx
// Prefer
const greeting = user.isAdmin ? "Welcome, admin" : `Hello ${user.name}`;
return <h1>{greeting}</h1>;

// Over
return <h1>{user.isAdmin ? "Welcome, admin" : `Hello ${user.name}`}</h1>;
```

## Imports

- React imports first: `import { useState } from "react"`
- Then third-party libs, then absolute project imports, then relative
- Type-only imports: `import type { ReactNode } from "react"` — never mix runtime and type imports in one statement when ESLint's `consistent-type-imports` is configured

## File Layout per Component

```
components/UserCard/
  UserCard.tsx
  UserCard.module.css   # or styled-components, or Tailwind classes inline
  UserCard.test.tsx
  index.ts              # re-export only
```

Inline single-file components are fine for trivial presentational pieces.
