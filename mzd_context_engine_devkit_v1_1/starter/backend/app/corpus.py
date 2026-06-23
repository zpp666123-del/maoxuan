from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

CORPUS_DIR_ENV = "MZD_CORPUS_DIR"
CORPUS_FOLDER_NAME = "Selected-Works-of-Mao-Zedong-JingHuo-version-main"
RELEASE_ID = "rel_mzd_jinghuo_local"
CANONICAL_EDITION = "静火版本《毛泽东选集》本地 Markdown 语料"
ANCHOR_SIZE = 4
TEXT_CHUNK_LIMIT = 720

PREFIX_RE = re.compile(r"^(\d{3})-(.+)$")
HEADING_RE = re.compile(r"^#+\s*(.+?)\s*$")
DATE_RE = re.compile(r"^（[^）]{2,80}）$")
SEPARATOR_RE = re.compile(r"^-{6,}$")
SPACE_RE = re.compile(r"[ \t]+")
PUNCTUATION = "。！？；：.!?;"


class ArticleNotFound(RuntimeError):
    pass


@dataclass(frozen=True)
class ArticleRef:
    article_id: str
    sequence: int
    title: str
    date_display: str
    volume_title: str
    section_title: str
    path: Path


def resolve_corpus_root() -> Path:
    configured = os.getenv(CORPUS_DIR_ENV)
    if configured:
        return Path(configured).expanduser().resolve()

    for parent in Path(__file__).resolve().parents:
        candidate = parent / CORPUS_FOLDER_NAME
        if candidate.exists():
            return candidate.resolve()

    return (Path(__file__).resolve().parents[4] / CORPUS_FOLDER_NAME).resolve()


def strip_prefix(value: str) -> str:
    match = PREFIX_RE.match(value)
    if match:
        return match.group(2).strip()
    return value.strip()


def article_sequence(path: Path) -> int:
    match = PREFIX_RE.match(path.stem)
    if not match:
        return 999999
    return int(match.group(1))


def clean_markdown_line(line: str) -> str:
    text = line.strip().strip("\ufeff")
    text = text.removeprefix(">").strip()
    text = SPACE_RE.sub(" ", text)
    return text.strip()


def split_long_text(text: str, limit: int = TEXT_CHUNK_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        if len(text) - start <= limit:
            chunks.append(text[start:].strip())
            break

        end = min(len(text), start + limit)
        search_end = min(len(text), end + 160)
        cut = -1
        for mark in PUNCTUATION:
            cut = max(cut, text.rfind(mark, start + limit // 2, search_end))
        if cut <= start:
            cut = end
        else:
            cut += 1

        chunk = text[start:cut].strip()
        if chunk:
            chunks.append(chunk)
        start = cut

    return chunks


def summarize_text(text: str, limit: int = 28) -> str:
    normalized = re.sub(r"\s+", "", text)
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def text_hash(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def read_article_header(path: Path, root: Path) -> ArticleRef:
    title = strip_prefix(path.stem)
    date_display = ""
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines()[:20]:
        line = clean_markdown_line(raw_line)
        if not line:
            continue
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group(1).strip()
            continue
        if not date_display and DATE_RE.match(line):
            date_display = line
            break

    relative_parts = path.relative_to(root).parts
    volume_title = strip_prefix(relative_parts[0]) if len(relative_parts) > 1 else "毛泽东选集"
    section_title = strip_prefix(relative_parts[1]) if len(relative_parts) > 2 else volume_title
    sequence = article_sequence(path)
    return ArticleRef(
        article_id=f"art_mzd_{sequence:03d}",
        sequence=sequence,
        title=title,
        date_display=date_display or "时间未标注",
        volume_title=volume_title,
        section_title=section_title,
        path=path,
    )


def parse_article(ref: ArticleRef) -> dict[str, Any]:
    raw_lines = ref.path.read_text(encoding="utf-8-sig").splitlines()
    text_chunks: list[str] = []
    title_seen = False
    date_seen = False

    for raw_line in raw_lines:
        line = clean_markdown_line(raw_line)
        if not line or SEPARATOR_RE.match(line):
            continue
        heading = HEADING_RE.match(line)
        if heading:
            if not title_seen:
                title_seen = True
                continue
            line = heading.group(1).strip()
        if not date_seen and DATE_RE.match(line):
            date_seen = True
            continue
        text_chunks.extend(split_long_text(line))

    if not text_chunks:
        raise ArticleNotFound(f"文章没有可读取正文：{ref.path.name}")

    article_token = f"mzd_{ref.sequence:03d}"
    paragraphs: list[dict[str, Any]] = []
    anchors: list[dict[str, Any]] = []

    for index, chunk in enumerate(text_chunks, start=1):
        anchor_index = (index - 1) // ANCHOR_SIZE + 1
        paragraph_id = f"p_{article_token}_{index:04d}"
        anchor_id = f"anc_{article_token}_{anchor_index:03d}"
        paragraphs.append(
            {
                "paragraphId": paragraph_id,
                "anchorId": anchor_id,
                "ordinal": index,
                "text": chunk,
                "textHash": text_hash(chunk),
            }
        )

    for offset in range(0, len(paragraphs), ANCHOR_SIZE):
        group = paragraphs[offset : offset + ANCHOR_SIZE]
        anchor_index = offset // ANCHOR_SIZE + 1
        first_text = group[0]["text"]
        anchors.append(
            {
                "anchorId": f"anc_{article_token}_{anchor_index:03d}",
                "title": f"第{anchor_index}组：{summarize_text(first_text)}",
                "paragraphIds": [item["paragraphId"] for item in group],
                "coreQuestion": f"这一组文字如何推进《{ref.title}》的核心问题？",
                "functionInArticle": "按原文顺序切分形成的阅读锚点，用于限制大模型只围绕当前局部生成。",
                "summary": None,
                "scenePreference": "none",
            }
        )

    full_text = "\n".join(item["text"] for item in paragraphs)
    return {
        "articleId": ref.article_id,
        "articleVersionId": f"av_mzd_{ref.sequence:03d}_jinghuo_local",
        "releaseId": RELEASE_ID,
        "currentReleaseId": RELEASE_ID,
        "slug": f"mzd-{ref.sequence:03d}",
        "title": ref.title,
        "canonicalEdition": CANONICAL_EDITION,
        "date": {"value": None, "endValue": None, "precision": "unknown", "display": ref.date_display},
        "dateDisplay": ref.date_display,
        "location": ref.section_title,
        "documentType": ref.volume_title,
        "volumeTitle": ref.volume_title,
        "sectionTitle": ref.section_title,
        "audience": None,
        "purpose": None,
        "coreQuestion": f"围绕《{ref.title}》理解其历史背景、当时处境与思想推理。",
        "textHash": text_hash(full_text),
        "paragraphCount": len(paragraphs),
        "anchors": anchors,
        "paragraphs": paragraphs,
    }


@lru_cache(maxsize=1)
def build_index(root_text: str) -> tuple[ArticleRef, ...]:
    root = Path(root_text)
    if not root.exists():
        return tuple()

    refs = [
        read_article_header(path, root)
        for path in root.rglob("*.md")
        if path.name.lower() != "readme.md"
    ]
    refs.sort(key=lambda item: (item.sequence, str(item.path)))
    return tuple(refs)


@lru_cache(maxsize=256)
def load_article(path_text: str, root_text: str) -> dict[str, Any]:
    root = Path(root_text)
    ref = read_article_header(Path(path_text), root)
    return parse_article(ref)


class LocalCorpusRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or resolve_corpus_root()).resolve()

    def refs(self) -> tuple[ArticleRef, ...]:
        return build_index(str(self.root))

    def list_articles(self) -> list[dict[str, Any]]:
        return [
            {
                "articleId": ref.article_id,
                "title": ref.title,
                "dateDisplay": ref.date_display,
                "documentType": ref.volume_title,
                "volumeTitle": ref.volume_title,
                "sectionTitle": ref.section_title,
                "coreQuestion": f"围绕《{ref.title}》理解其历史背景、当时处境与思想推理。",
                "currentReleaseId": RELEASE_ID,
            }
            for ref in self.refs()
        ]

    def get_article(self, article_id: str, release_id: str) -> dict[str, Any]:
        if release_id != RELEASE_ID:
            raise ArticleNotFound("article/release not found")

        ref = next((item for item in self.refs() if item.article_id == article_id), None)
        if not ref:
            raise ArticleNotFound("article/release not found")
        return load_article(str(ref.path), str(self.root))

    def has_anchor(self, article_id: str, release_id: str, anchor_id: str) -> bool:
        article = self.get_article(article_id, release_id)
        return any(anchor["anchorId"] == anchor_id for anchor in article["anchors"])


corpus = LocalCorpusRepository()
