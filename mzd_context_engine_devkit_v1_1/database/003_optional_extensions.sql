-- 可选能力。按实际部署启用，不是 MVP 启动的硬依赖。

-- 1) 三元组近似搜索需要 pg_trgm；如果执行 002_indexes.sql，请先启用：
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2) 地理能力：
-- CREATE EXTENSION IF NOT EXISTS postgis;
-- ALTER TABLE places ADD COLUMN geom geometry(Geometry, 4326);
-- UPDATE places SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude),4326)
-- WHERE longitude IS NOT NULL AND latitude IS NOT NULL;
-- CREATE INDEX idx_places_geom ON places USING gist (geom);

-- 3) 语义检索：
-- CREATE EXTENSION IF NOT EXISTS vector;
-- ALTER TABLE context_units ADD COLUMN embedding vector(<dimension>);
-- CREATE INDEX idx_context_units_embedding ON context_units USING hnsw (embedding vector_cosine_ops);
-- 向量维度和索引参数应与团队选定的嵌入模型一起锁定。
