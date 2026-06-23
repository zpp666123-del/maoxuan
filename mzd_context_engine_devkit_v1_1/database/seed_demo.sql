-- 本地静火版语料的最小种子数据。完整正文由 starter/backend/app/corpus.py 从 Markdown 目录读取。

INSERT INTO collections (id, slug, title, description, status)
VALUES ('col_mzd_jinghuo', 'mzd-jinghuo', '静火版本《毛泽东选集》', '本地 Markdown 语料集合。', 'published')
ON CONFLICT DO NOTHING;

INSERT INTO articles (id, collection_id, slug, title, status)
VALUES ('art_mzd_001', 'col_mzd_jinghuo', 'mzd-001', '中国社会各阶级的分析', 'published')
ON CONFLICT DO NOTHING;

INSERT INTO article_versions (
  id, article_id, version_label, article_date, date_precision,
  location_text, location_precision, document_type, audience, purpose,
  core_question, text_hash, status
) VALUES (
  'av_mzd_001_jinghuo_local', 'art_mzd_001', '静火本地 Markdown', '1925-12-01', 'day',
  '第一次国内革命战争时期', 'unknown', 'essay', NULL, NULL,
  '围绕《中国社会各阶级的分析》理解其历史背景、当时处境与思想推理。',
  'sha256:0000000000000000000000000000000000000000000000000000000000000001', 'published'
) ON CONFLICT DO NOTHING;

UPDATE articles SET default_version_id = 'av_mzd_001_jinghuo_local' WHERE id = 'art_mzd_001';
