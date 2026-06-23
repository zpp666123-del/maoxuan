# Productization Requirements

## Scope

This spec turns the current historical reading prototype into a productized software system. It keeps the current center-reader interaction model, real LLM-only runtime, agent/subagent workflows, image generation path, and local JingHuo corpus as the baseline.

## User Stories

1. As a reader, I want the book text to stay in the most comfortable central reading position so that AI tools do not interrupt long-form reading.
2. As a reader, I want named tool buttons to open focused modals so that maps, timelines, people, events, and illustrations are available on demand.
3. As a reader, I want previously generated workflow results to survive app restarts so that I do not pay model cost twice for the same article exploration.
4. As a reader, I want article-level overview and map variables to be prepared automatically when API is configured so that opening a tool does not feel like starting from a cold wait.
5. As an operator, I want missing API configuration to fail explicitly so that the product never serves static or fake AI output.
6. As a product owner, I want a staged acceptance plan so that each release can be verified against product value rather than isolated technical tasks.

## Acceptance Criteria

1. When the app loads an article, the system shall render the article body as the central primary surface.
2. When the user clicks a named exploration button, the system shall open a modal; map opens with the prebuilt map framework immediately, while AI enhancement buttons start the corresponding backend workflow.
3. When a workflow commits an artifact, the system shall persist the artifact with a deterministic cache key based on article, anchor, workflow, and target.
4. When the same workflow is requested again without `forceRegenerate`, the system shall replay the persisted artifact instead of calling the model again.
5. When `forceRegenerate` is true, the system shall bypass the persisted artifact and call the configured real model path.
6. When API credentials or model names are missing, the system shall emit a failure event and shall not fabricate substitute content.
7. When `map_context` commits, the system shall emit `map.variables.committed` so the prebuilt map variable layer can refresh without parsing arbitrary UI text.
8. When API is configured and automatic generation is enabled, article load shall start background prewarm workflows for the article overview and map context without opening a waiting modal.
9. When package validation runs, the system shall pass schema, starter tests, and manifest checks.

## Non-Goals For This Increment

- Full multi-user authentication.
- Production PostgreSQL migration execution.
- Admin review studio completion.
- Hosted deployment automation.
