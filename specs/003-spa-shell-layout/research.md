# Research: SPA Shell Layout

**Feature Branch**: `003-spa-shell-layout`
**Date**: 2026-02-11

## Decision 1: HTMX Multi-Target Swap Pattern

**Decision**: Use `hx-target` for the primary swap, plus `hx-swap-oob` in the server response for secondary panel updates.

**Rationale**: Clicking a seller in Left1 must update Left2 (events) and optionally clear Main (lots). With `hx-target="#panel-left2"` on the seller link, the primary response swaps into Left2. The server response includes an OOB fragment `<div id="panel-main" hx-swap-oob="innerHTML">...</div>` to clear or update Main simultaneously. This is a single HTTP request — no extensions, no custom JS.

**Alternatives Considered**:
- `hx-select-oob` (client-side extraction): Less explicit; harder to debug since the template doesn't declare what it updates.
- `multi-swap` extension: Third-party dependency for something OOB handles natively.
- Separate HTMX requests per panel: Doubles round trips, creates race conditions.
- `hx-swap="none"` + all OOB: Works but unintuitive — no primary target makes debugging harder.

## Decision 2: HTMX Request Cancellation

**Decision**: Use `hx-sync="this:replace"` on each panel container, inherited by all child elements.

**Rationale**: Without `hx-sync`, clicking Seller A then Seller B fires parallel requests. Whichever finishes last wins the DOM swap — a race condition. The `replace` strategy on the panel container aborts the in-flight request and replaces it with the new one. Applied via inheritance on `#panel-left1`, it covers all seller links automatically.

**Alternatives Considered**:
- `drop` strategy: Ignores new clicks while in-flight — confusing UX.
- `queue last`: Waits for first request to finish, adding latency.
- No `hx-sync`: Race condition. Unacceptable.
- JavaScript `htmx:abort` event: Requires manual tracking. `hx-sync` is declarative.

## Decision 3: CSS Three-Column Layout

**Decision**: CSS Grid with `grid-template-columns: 250px 300px 1fr`, `grid-template-rows: auto 1fr`, `height: 100vh` on the shell container, and `min-height: 0; overflow-y: auto` on each panel.

**Rationale**: CSS Grid handles both the navbar row and three-column panel row in a single layout context. `100vh` constrains to viewport, enabling independent scroll on each panel. `min-height: 0` is critical — without it, grid children default to `min-height: auto`, which prevents overflow scrolling.

**Alternatives Considered**:
- Flexbox: Requires two nested containers (vertical + horizontal). Grid is more direct.
- `position: fixed` panels: Fragile, breaks with dynamic navbar heights.
- `100dvh`: Unnecessary for desktop-first SPA. `100vh` has broader support.

## Decision 4: Django Partial Template Pattern

**Decision**: Separate URL endpoints for panel fragments. No `HX-Request` header checking. Use `{% include %}` for template reuse between the full shell page and fragment endpoints.

**Rationale**: Each URL returns exactly one thing — a full page or a fragment. No branching logic in views. Contract tests hit fragment endpoints directly. No third-party packages required.

**Alternatives Considered**:
- Single view with `HX-Request` header check: Introduces branching, ambiguity, and `Vary: HX-Request` caching complexity.
- `django-template-partials`: Dependency for syntactic sugar over `{% include %}`.
- `django-render-block`: Parses full template even when only a block is needed.
- `django-htmx` middleware: No value when not checking headers.

## Decision 5: Visual Design Direction

**Decision**: Evolve the existing design system (system font stack, blue/slate palette, card-based components) into a polished product-quality UI. Keep the existing color foundation (#2563eb primary, #1e293b dark) but refine spacing, typography scale, panel headers, selection states, and transitions.

**Rationale**: The current CSS is a solid functional foundation with clean structure. Rather than replacing it with a framework (Tailwind, Bootstrap), we refine what exists. This avoids dependency bloat, keeps the CSS maintainable, and preserves continuity with existing pages (lot detail, override, import) that remain outside the SPA shell.

**Alternatives Considered**:
- Tailwind CSS: Would require build tooling (PostCSS, npm). The project uses CDN-only dependencies. Adding a build step is scope creep.
- Bootstrap: Opinionated grid system would conflict with our CSS Grid shell. Heavy CSS payload for components we don't need.
- Complete redesign: Unnecessary. The existing palette and component patterns are professional. They need refinement, not replacement.

## Summary

| Topic | Decision | Key Dependency |
|-------|----------|---------------|
| Multi-target swap | `hx-target` + `hx-swap-oob` | HTMX 2.0.4 (already installed) |
| Request cancellation | `hx-sync="this:replace"` | HTMX 2.0.4 (already installed) |
| CSS layout | CSS Grid, `100vh`, `min-height: 0` | No dependencies |
| Django partials | Separate endpoints + `{% include %}` | No dependencies |
| Visual design | Evolve existing CSS | No dependencies |
