# Phase 02 Deferred Items

## Pre-existing Issues (Out of Scope)

### vite.config.ts TypeScript build errors

**Discovered:** Plan 07 (Task 2)
**Error:**
```
vite.config.ts(3,18): error TS2307: Cannot find module 'path' or its corresponding type declarations.
vite.config.ts(8,32): error TS2304: Cannot find name '__dirname'.
```
**Cause:** `frontend/tsconfig.node.json` uses `"lib": ["ES2023"]` but does not declare `@types/node` in compilerOptions. The `path` module and `__dirname` are Node.js globals.
**Impact:** `npm run build` (which runs `tsc -b`) fails on vite.config.ts. The app TypeScript (`npx tsc --noEmit` targeting app files) compiles cleanly.
**Fix:** Add `"types": ["node"]` to `tsconfig.node.json` compilerOptions, or install `@types/node` as a dev dependency.
**Status:** Deferred — pre-existing from Phase 0 scaffold. Not caused by Phase 2 changes.
