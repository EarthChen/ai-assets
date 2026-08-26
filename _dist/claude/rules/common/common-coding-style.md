---
description: "ECC coding style: design principles, immutability, file organization, error handling, validation"
alwaysApply: true
---
# Coding Style

## Design Principles

- Follow DRY, KISS, SOLID, and YAGNI when coding
- A bug report names one symptom; trace every caller of the code you touch, find the shared cause, fix it once
- Mark deliberate simplifications with a known ceiling (global lock, O(n²) scan, naive heuristic) using a `ceiling:` comment naming the ceiling and the upgrade path

## Immutability (CRITICAL)

In NEW code, create new objects instead of mutating existing ones. In existing codebases that mutate in place, follow the codebase's convention:

```
// Pseudocode
WRONG:  modify(original, field, value) → changes original in-place
CORRECT: update(original, field, value) → returns new copy with change
```

## File Organization

MANY SMALL FILES > FEW LARGE FILES:

- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Extract utilities from large modules
- Organize by feature/domain, not by type

## Error Handling

ALWAYS handle errors comprehensively:

- Handle errors explicitly at every level
- Provide user-friendly error messages in UI-facing code
- Log detailed error context on the server side
- Never silently swallow errors

## Input Validation

ALWAYS validate at system boundaries:

- Use schema-based validation where available
- Fail fast with clear error messages
- Never trust external data (API responses, user input, file content)
