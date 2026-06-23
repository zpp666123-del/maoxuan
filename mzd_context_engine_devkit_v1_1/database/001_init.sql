-- 毛泽东著作历史情境化阅读引擎：PostgreSQL 基线结构
-- 说明：第一阶段使用 text 业务 ID，便于导入导出与跨环境稳定。

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE publication_status AS ENUM ('draft', 'review', 'published', 'archived');
CREATE TYPE visibility_level AS ENUM ('public', 'internal', 'private');
CREATE TYPE review_status AS ENUM ('machine_candidate', 'draft', 'approved', 'rejected', 'archived');
CREATE TYPE reading_mode AS ENUM ('balanced', 'time_frozen', 'aftereffects', 'thought_lineage');
CREATE TYPE interaction_status AS ENUM ('accepted', 'running', 'completed', 'degraded', 'failed', 'cancelled');
CREATE TYPE feedback_status AS ENUM ('open', 'triaged', 'in_progress', 'resolved', 'closed');

CREATE TABLE collections (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    status publication_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE articles (
    id TEXT PRIMARY KEY,
    collection_id TEXT REFERENCES collections(id),
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    default_version_id TEXT,
    current_release_id TEXT,
    status publication_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE article_versions (
    id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE RESTRICT,
    version_label TEXT NOT NULL,
    imported_from TEXT,
    article_date TEXT,
    date_precision TEXT NOT NULL CHECK (date_precision IN ('day','month','year','range','unknown')),
    date_end TEXT,
    location_text TEXT,
    location_precision TEXT CHECK (location_precision IN ('exact','approximate','region','unknown')),
    document_type TEXT NOT NULL CHECK (document_type IN ('essay','speech','report','letter','directive','comment','preface','other')),
    audience TEXT,
    purpose TEXT,
    core_question TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    status publication_status NOT NULL DEFAULT 'draft',
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(article_id, text_hash)
);

ALTER TABLE articles
    ADD CONSTRAINT fk_articles_default_version
    FOREIGN KEY (default_version_id) REFERENCES article_versions(id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE paragraphs (
    id TEXT PRIMARY KEY,
    article_version_id TEXT NOT NULL REFERENCES article_versions(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    text TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    entity_spans JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(article_version_id, ordinal)
);

CREATE TABLE anchors (
    id TEXT PRIMARY KEY,
    article_version_id TEXT NOT NULL REFERENCES article_versions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    start_ordinal INTEGER NOT NULL CHECK (start_ordinal > 0),
    end_ordinal INTEGER NOT NULL CHECK (end_ordinal >= start_ordinal),
    core_question TEXT NOT NULL,
    function_in_article TEXT NOT NULL,
    summary TEXT,
    scene_preference TEXT NOT NULL DEFAULT 'none' CHECK (scene_preference IN ('none','timeline','decision','map','relations')),
    status publication_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(article_version_id, start_ordinal, end_ordinal)
);

CREATE TABLE context_packs (
    id TEXT PRIMARY KEY,
    article_version_id TEXT NOT NULL REFERENCES article_versions(id) ON DELETE RESTRICT,
    current_version_id TEXT,
    status publication_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE context_pack_versions (
    id TEXT PRIMARY KEY,
    context_pack_id TEXT NOT NULL REFERENCES context_packs(id) ON DELETE RESTRICT,
    version TEXT NOT NULL,
    cutoff_date TEXT,
    summary TEXT,
    content_hash TEXT NOT NULL,
    status publication_status NOT NULL DEFAULT 'draft',
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(context_pack_id, version)
);

ALTER TABLE context_packs
    ADD CONSTRAINT fk_context_packs_current_version
    FOREIGN KEY (current_version_id) REFERENCES context_pack_versions(id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    context_pack_version_id TEXT REFERENCES context_pack_versions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    creator TEXT,
    publication_date TEXT,
    locator TEXT,
    citation_label TEXT,
    reliability CHAR(1) NOT NULL CHECK (reliability IN ('A','B','C','D')),
    rights_status TEXT NOT NULL DEFAULT 'unknown' CHECK (rights_status IN ('public','licensed_public','internal_only','restricted_excerpt','unknown')),
    visibility visibility_level NOT NULL DEFAULT 'internal',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    context_pack_version_id TEXT REFERENCES context_pack_versions(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('person','organization','concept','event_group')),
    canonical_name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    description TEXT,
    visibility visibility_level NOT NULL DEFAULT 'internal',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE places (
    id TEXT PRIMARY KEY,
    context_pack_version_id TEXT REFERENCES context_pack_versions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    longitude DOUBLE PRECISION CHECK (longitude BETWEEN -180 AND 180),
    latitude DOUBLE PRECISION CHECK (latitude BETWEEN -90 AND 90),
    precision TEXT NOT NULL CHECK (precision IN ('exact','approximate','region','unknown')),
    description TEXT,
    structured_geometry JSONB,
    visibility visibility_level NOT NULL DEFAULT 'internal',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE context_units (
    id TEXT PRIMARY KEY,
    context_pack_version_id TEXT NOT NULL REFERENCES context_pack_versions(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('event','actor_state','constraint','debate','option','concept','place','statistic','outcome','question','reasoning_clue')),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    details TEXT,
    valid_from TEXT,
    valid_to TEXT,
    known_at TEXT,
    time_relation TEXT NOT NULL CHECK (time_relation IN ('long_term','before_writing','at_writing','after_writing','timeless','unknown')),
    fact_interpretation TEXT NOT NULL CHECK (fact_interpretation IN ('fact','interpretation','inference','question')),
    confidence TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    editorial_status review_status NOT NULL DEFAULT 'draft',
    visibility visibility_level NOT NULL DEFAULT 'internal',
    structured_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    editor_note TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE context_unit_sources (
    context_unit_id TEXT NOT NULL REFERENCES context_units(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
    purpose TEXT,
    PRIMARY KEY (context_unit_id, source_id)
);

CREATE TABLE context_unit_entities (
    context_unit_id TEXT NOT NULL REFERENCES context_units(id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE RESTRICT,
    role TEXT,
    PRIMARY KEY (context_unit_id, entity_id)
);

CREATE TABLE context_unit_places (
    context_unit_id TEXT NOT NULL REFERENCES context_units(id) ON DELETE CASCADE,
    place_id TEXT NOT NULL REFERENCES places(id) ON DELETE RESTRICT,
    role TEXT,
    PRIMARY KEY (context_unit_id, place_id)
);

CREATE TABLE context_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anchor_id TEXT NOT NULL REFERENCES anchors(id) ON DELETE CASCADE,
    context_unit_id TEXT NOT NULL REFERENCES context_units(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('precondition','trigger','explains_background','explains_situation','supports_reasoning','contrasts_reasoning','defines_concept','spatial_context','later_outcome')),
    relevance NUMERIC(4,3) NOT NULL CHECK (relevance BETWEEN 0 AND 1),
    priority INTEGER NOT NULL DEFAULT 10 CHECK (priority BETWEEN 0 AND 100),
    slot_hints TEXT[] NOT NULL DEFAULT '{}',
    scene_hints TEXT[] NOT NULL DEFAULT '{}',
    editor_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(anchor_id, context_unit_id, role)
);

CREATE TABLE prompt_versions (
    id TEXT PRIMARY KEY,
    prompt_key TEXT NOT NULL,
    version TEXT NOT NULL,
    role TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    text_body TEXT NOT NULL,
    output_schema_id TEXT,
    model_policy TEXT,
    status publication_status NOT NULL DEFAULT 'draft',
    evaluation_report JSONB,
    git_commit TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(prompt_key, version)
);

CREATE TABLE prompt_bundles (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    prompt_map JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    status publication_status NOT NULL DEFAULT 'draft',
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workflow_versions (
    id TEXT PRIMARY KEY,
    workflow_key TEXT NOT NULL,
    version TEXT NOT NULL,
    definition JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    status publication_status NOT NULL DEFAULT 'draft',
    evaluation_report JSONB,
    git_commit TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(workflow_key, version)
);

CREATE TABLE releases (
    id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(id),
    article_version_id TEXT NOT NULL REFERENCES article_versions(id),
    context_pack_version_id TEXT NOT NULL REFERENCES context_pack_versions(id),
    prompt_bundle_id TEXT NOT NULL REFERENCES prompt_bundles(id),
    workflow_version_id TEXT NOT NULL REFERENCES workflow_versions(id),
    status TEXT NOT NULL CHECK (status IN ('active','superseded','rolled_back','archived')),
    release_notes TEXT,
    published_by TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    supersedes_release_id TEXT REFERENCES releases(id)
);

ALTER TABLE articles
    ADD CONSTRAINT fk_articles_current_release
    FOREIGN KEY (current_release_id) REFERENCES releases(id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE reading_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    release_id TEXT NOT NULL REFERENCES releases(id),
    article_id TEXT NOT NULL REFERENCES articles(id),
    current_anchor_id TEXT REFERENCES anchors(id),
    mode reading_mode NOT NULL DEFAULT 'balanced',
    ui_version INTEGER NOT NULL DEFAULT 1,
    client_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE interaction_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES reading_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('anchor_changed','paragraph_clicked','text_selected','entity_clicked','mode_changed','question_submitted')),
    release_id TEXT NOT NULL REFERENCES releases(id),
    article_id TEXT NOT NULL REFERENCES articles(id),
    anchor_id TEXT NOT NULL REFERENCES anchors(id),
    paragraph_id TEXT REFERENCES paragraphs(id),
    selection JSONB,
    entity_id TEXT,
    entity_type TEXT,
    mode reading_mode NOT NULL,
    question_ciphertext BYTEA,
    normalized_event JSONB NOT NULL,
    input_hash TEXT,
    idempotency_key TEXT,
    ui_version INTEGER NOT NULL,
    status interaction_status NOT NULL DEFAULT 'accepted',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    UNIQUE(session_id, idempotency_key)
);

CREATE TABLE generation_runs (
    id TEXT PRIMARY KEY,
    interaction_id TEXT NOT NULL REFERENCES interaction_events(id) ON DELETE CASCADE,
    parent_run_id TEXT REFERENCES generation_runs(id),
    release_id TEXT NOT NULL REFERENCES releases(id),
    workflow_version_id TEXT NOT NULL REFERENCES workflow_versions(id),
    prompt_bundle_id TEXT NOT NULL REFERENCES prompt_bundles(id),
    input_hash TEXT,
    planner_output JSONB,
    retrieved_context_unit_ids TEXT[] NOT NULL DEFAULT '{}',
    source_ids TEXT[] NOT NULL DEFAULT '{}',
    model_runs JSONB NOT NULL DEFAULT '[]'::jsonb,
    validation_report JSONB,
    final_output JSONB,
    status interaction_status NOT NULL DEFAULT 'running',
    timings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE feedback (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES reading_sessions(id) ON DELETE SET NULL,
    interaction_id TEXT REFERENCES interaction_events(id) ON DELETE SET NULL,
    release_id TEXT REFERENCES releases(id),
    article_id TEXT REFERENCES articles(id),
    anchor_id TEXT REFERENCES anchors(id),
    target_type TEXT NOT NULL CHECK (target_type IN ('article','anchor','slot','scene','answer')),
    target_id TEXT NOT NULL,
    category TEXT NOT NULL,
    comment_ciphertext BYTEA,
    status feedback_status NOT NULL DEFAULT 'open',
    severity TEXT CHECK (severity IN ('P0','P1','P2','P3')),
    assigned_to TEXT,
    resolution TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE content_gaps (
    id TEXT PRIMARY KEY,
    context_pack_version_id TEXT NOT NULL REFERENCES context_pack_versions(id) ON DELETE CASCADE,
    anchor_id TEXT REFERENCES anchors(id),
    gap_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('blocking','high','medium','low')),
    status TEXT NOT NULL CHECK (status IN ('open','in_progress','resolved','wont_fix')),
    assigned_to TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id TEXT,
    actor_role TEXT,
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT,
    before_hash TEXT,
    after_hash TEXT,
    reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
