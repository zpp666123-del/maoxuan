# 数据库

执行顺序：

```bash
psql "$DATABASE_URL" -f database/001_init.sql
psql "$DATABASE_URL" -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;'
psql "$DATABASE_URL" -f database/002_indexes.sql
# 按需执行 003_optional_extensions.sql 中的部分
```

说明：

- `002_indexes.sql` 使用 `pg_trgm`，需先启用扩展；
- PostGIS 与 pgvector 为可选能力；
- 生产环境应使用 migration 工具执行，而不是手工跑整文件；
- 示例 SQL 未包含具体身份表，可与现有 OIDC/用户系统对接；
- `question_ciphertext` 和 `comment_ciphertext` 表示敏感文本应按项目密钥策略加密，示例骨架未实现。

