BEGIN;

CREATE INDEX idx_article_versions_article ON article_versions(article_id, created_at DESC);
CREATE INDEX idx_paragraphs_version_ordinal ON paragraphs(article_version_id, ordinal);
CREATE INDEX idx_anchors_version_range ON anchors(article_version_id, start_ordinal, end_ordinal);
CREATE INDEX idx_context_pack_versions_pack ON context_pack_versions(context_pack_id, created_at DESC);
CREATE INDEX idx_context_units_pack_type_status ON context_units(context_pack_version_id, type, editorial_status);
CREATE INDEX idx_context_units_known_at ON context_units(known_at);
CREATE INDEX idx_context_links_anchor_relevance ON context_links(anchor_id, relevance DESC, priority ASC);
CREATE INDEX idx_context_links_unit ON context_links(context_unit_id);
CREATE INDEX idx_sources_pack_visibility ON sources(context_pack_version_id, visibility, reliability);
CREATE INDEX idx_releases_article_published ON releases(article_id, published_at DESC);
CREATE INDEX idx_sessions_release_updated ON reading_sessions(release_id, updated_at DESC);
CREATE INDEX idx_interactions_session_created ON interaction_events(session_id, created_at DESC);
CREATE INDEX idx_interactions_status_created ON interaction_events(status, created_at DESC);
CREATE INDEX idx_runs_interaction ON generation_runs(interaction_id, created_at DESC);
CREATE INDEX idx_runs_status_created ON generation_runs(status, created_at DESC);
CREATE INDEX idx_feedback_status_severity ON feedback(status, severity, created_at DESC);
CREATE INDEX idx_gaps_pack_status ON content_gaps(context_pack_version_id, status, severity);
CREATE INDEX idx_audit_object ON audit_logs(object_type, object_id, occurred_at DESC);

-- 可选全文索引；中文分词策略需按部署环境调整。
CREATE INDEX idx_paragraphs_text_trgm ON paragraphs USING gin (text gin_trgm_ops);
CREATE INDEX idx_context_units_text_trgm ON context_units USING gin ((title || ' ' || summary || ' ' || coalesce(details,'')) gin_trgm_ops);

COMMIT;
