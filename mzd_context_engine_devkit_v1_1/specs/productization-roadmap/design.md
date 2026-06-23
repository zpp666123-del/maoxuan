# Productization Design

## Architecture Direction

The product should move from prototype runtime state toward a durable local-first system:

- Reader UI: center-first text, named tool buttons, modal exploration.
- Backend workflows: real LLM and image API only, with explicit failure events when configuration is missing.
- Artifact persistence: SQLite in the starter app for local product use, later replaceable by PostgreSQL.
- Generated images: saved as local generated assets and referenced by URL.
- Cache policy: deterministic cache key, explicit `forceRegenerate`, no static answer path.

## Persistence Boundary

The starter backend stores workflow artifacts in SQLite with a JSON payload:

- `cache_key`: deterministic key from release, article, anchor, workflow, target, and mode.
- `artifact_json`: committed agent artifact and optional generated image metadata.
- `created_at` / `updated_at`: operational timestamps.

The in-memory dictionary remains as a hot cache, but SQLite is the source for restart recovery.

## Upgrade Path

1. SQLite artifact persistence in starter backend.
2. PostgreSQL table compatible with the same key/payload shape.
3. Run history query APIs for product UI.
4. Operator dashboard for model errors, cost, and artifact review.

## Testing Strategy

- Unit test SQLite artifact roundtrip.
- Smoke test cached workflow replay.
- Browser test center reader and modal workflow entry.
- Package validation after manifest regeneration.
