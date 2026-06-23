# ADR-004：PostgreSQL 是第一阶段权威数据源

状态：Accepted

## 背景

项目涉及关系、版本、审核、时间、全文、JSON 和可选地理/向量数据。过早引入多个数据库会增加一致性与运维成本。

## 决策

文章、ContextPack、链接、运行记录、运行和审计存 PostgreSQL；PostGIS 和 pgvector 按需启用。Redis、搜索索引和图谱均可重建。

## 后果

MVP 简化。若检索或图谱规模增长，可新增专用投影，不改变规范数据主源。

