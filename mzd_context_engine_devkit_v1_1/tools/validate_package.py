#!/usr/bin/env python3
"""Validate the development kit without network access.

Checks:
- required package files and rendered diagrams;
- JSON/YAML parsing;
- JSON Schema examples and relative references;
- core cross-object business invariants;
- starter Python compilation and smoke tests;
- optional manifest integrity when MANIFEST.sha256 exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
warnings.filterwarnings("ignore", message="jsonschema.RefResolver is deprecated.*", category=DeprecationWarning)
from jsonschema import Draft202012Validator, FormatChecker, RefResolver


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "specs" / "json-schema"
EXAMPLES_DIR = ROOT / "examples"
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".git", ".venv", ".local", "generated", "node_modules"}


@dataclass
class ValidationReport:
    passed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def ok(self, message: str) -> None:
        self.passed.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def fail(self, message: str) -> None:
        self.errors.append(message)

    @property
    def success(self) -> bool:
        return not self.errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def included_file(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not any(part in EXCLUDED_PARTS for part in relative.parts)


def iter_refs(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str):
                yield item
            else:
                yield from iter_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_refs(item)


def validate_required_files(report: ValidationReport) -> None:
    required = [
        "README.md",
        "PACKAGE_INDEX.md",
        "PRD.md",
        "ARCHITECTURE.md",
        "docs/02_UI_IA.md",
        "docs/05_AI_PROMPTS_WORKFLOWS.md",
        "docs/06_CONTEXTPACK.md",
        "specs/openapi.yaml",
        "specs/prompts.yaml",
        "specs/reading-workflow.yaml",
        "specs/content-workflow.yaml",
        "database/001_init.sql",
        "starter/README.md",
        "tests/prompt-eval-cases.yaml",
        "tools/render_diagrams.sh",
    ]
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        report.fail(f"缺少必需文件: {', '.join(missing)}")
    else:
        report.ok(f"必需文件齐全（{len(required)} 项）")

    for index in range(1, 13):
        prefix = f"{index:02d}_"
        dot = list((ROOT / "diagrams").glob(f"{prefix}*.dot"))
        svg = list((ROOT / "diagrams").glob(f"{prefix}*.svg"))
        png = list((ROOT / "diagrams").glob(f"{prefix}*.png"))
        mmd = list((ROOT / "diagrams").glob(f"{prefix}*.mmd"))
        if not (dot and svg and png and mmd):
            report.fail(
                f"图 {index:02d} 资产不完整：dot={len(dot)}, svg={len(svg)}, "
                f"png={len(png)}, mmd={len(mmd)}"
            )
    if not any(message.startswith("图 ") for message in report.errors):
        report.ok("12 张框图均包含 DOT、Mermaid、SVG、PNG")


def validate_parsing(report: ValidationReport) -> None:
    json_paths = sorted(path for path in ROOT.rglob("*.json") if included_file(path))
    yaml_paths = sorted(path for path in [*ROOT.rglob("*.yaml"), *ROOT.rglob("*.yml")] if included_file(path))
    for path in json_paths:
        try:
            load_json(path)
        except Exception as exc:  # noqa: BLE001
            report.fail(f"JSON 解析失败 {path.relative_to(ROOT)}: {exc}")
    for path in yaml_paths:
        try:
            load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            report.fail(f"YAML 解析失败 {path.relative_to(ROOT)}: {exc}")
    if not any("解析失败" in message for message in report.errors):
        report.ok(f"JSON/YAML 均可解析（JSON {len(json_paths)}，YAML {len(yaml_paths)}）")


def validate_schema_files(report: ValidationReport) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        try:
            schema = load_json(path)
            Draft202012Validator.check_schema(schema)
            schemas[path.name] = schema
        except Exception as exc:  # noqa: BLE001
            report.fail(f"Schema 无效 {path.name}: {exc}")
    if schemas and not any("Schema 无效" in message for message in report.errors):
        report.ok(f"JSON Schema 元模式校验通过（{len(schemas)} 个）")
    return schemas


def validate_local_refs(report: ValidationReport) -> None:
    candidates = [
        *SCHEMA_DIR.glob("*.json"),
        ROOT / "specs" / "openapi.yaml",
    ]
    missing: list[str] = []
    for path in candidates:
        document = load_json(path) if path.suffix == ".json" else load_yaml(path)
        for ref in iter_refs(document):
            if ref.startswith("#") or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", ref):
                continue
            ref_file = ref.split("#", 1)[0]
            if not ref_file:
                continue
            target = (path.parent / ref_file).resolve()
            if not target.is_file():
                missing.append(f"{path.relative_to(ROOT)} -> {ref}")
    if missing:
        report.fail("无法解析的本地 $ref: " + "; ".join(missing))
    else:
        report.ok("JSON Schema 与 OpenAPI 的本地 $ref 均存在")


def schema_validate(instance_path: Path, schema_name: str) -> list[str]:
    schema_path = SCHEMA_DIR / schema_name
    schema = load_json(schema_path)
    instance = load_json(instance_path)
    resolver = RefResolver(base_uri=SCHEMA_DIR.resolve().as_uri() + "/", referrer=schema)
    validator = Draft202012Validator(
        schema,
        resolver=resolver,
        format_checker=FormatChecker(),
    )
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        loc = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{loc}: {error.message}")
    return errors


def validate_examples(report: ValidationReport) -> None:
    mappings = {
        "mzd_article_sample.json": "article.schema.json",
        "mzd_context_pack_sample.json": "context-pack.schema.json",
        "mzd_interaction_sample.json": "interaction-event.schema.json",
        "mzd_generation_run_sample.json": "generation-run.schema.json",
    }
    failures = 0
    for filename, schema_name in mappings.items():
        path = EXAMPLES_DIR / filename
        if not path.is_file():
            report.fail(f"缺少示例 {filename}")
            failures += 1
            continue
        errors = schema_validate(path, schema_name)
        if errors:
            failures += 1
            report.fail(f"示例 {filename} 未通过 {schema_name}: " + " | ".join(errors[:12]))
    if failures == 0:
        report.ok(f"示例 JSON 均通过对应 Schema（{len(mappings)} 个）")


def validate_cross_object_invariants(report: ValidationReport) -> None:
    article = load_json(EXAMPLES_DIR / "mzd_article_sample.json")
    context = load_json(EXAMPLES_DIR / "mzd_context_pack_sample.json")

    paragraph_ids = {p["paragraphId"] for p in article["paragraphs"]}
    anchor_ids = {a["anchorId"] for a in article["anchors"]}
    anchor_paragraphs = [pid for a in article["anchors"] for pid in a["paragraphIds"]]

    if set(anchor_paragraphs) != paragraph_ids:
        report.fail("示例锚点未完整覆盖全部段落")
    if len(anchor_paragraphs) != len(set(anchor_paragraphs)):
        report.fail("示例锚点存在段落重叠")
    unknown_anchor_paragraphs = set(anchor_paragraphs) - paragraph_ids
    if unknown_anchor_paragraphs:
        report.fail(f"锚点引用不存在段落: {sorted(unknown_anchor_paragraphs)}")

    if article["articleId"] != context["articleId"]:
        report.fail("Article 与 ContextPack 的 articleId 不一致")
    if article["articleVersionId"] != context["articleVersionId"]:
        report.fail("Article 与 ContextPack 的 articleVersionId 不一致")

    source_ids = {item["sourceId"] for item in context["sources"]}
    unit_ids = {item["contextUnitId"] for item in context["units"]}
    entity_ids = {item["entityId"] for item in context["entities"]}
    place_ids = {item["placeId"] for item in context["places"]}

    for unit in context["units"]:
        missing_sources = set(unit.get("sourceIds", [])) - (source_ids | paragraph_ids)
        missing_entities = set(unit.get("entityIds", [])) - entity_ids
        missing_places = set(unit.get("placeIds", [])) - place_ids
        if missing_sources:
            report.fail(f"{unit['contextUnitId']} 引用不存在来源: {sorted(missing_sources)}")
        if missing_entities:
            report.fail(f"{unit['contextUnitId']} 引用不存在实体: {sorted(missing_entities)}")
        if missing_places:
            report.fail(f"{unit['contextUnitId']} 引用不存在地点: {sorted(missing_places)}")

    for link in context["links"]:
        if link["anchorId"] not in anchor_ids:
            report.fail(f"Context link 引用不存在锚点: {link['anchorId']}")
        if link["contextUnitId"] not in unit_ids:
            report.fail(f"Context link 引用不存在单元: {link['contextUnitId']}")

    if not any(
        token in message
        for message in report.errors
        for token in [
            "示例锚点", "Article 与", "引用不存在"
        ]
    ):
        report.ok("跨对象业务不变量校验通过")


def collect_source_ids(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "sourceIds" and isinstance(item, list):
                result.update(str(x) for x in item)
            else:
                result.update(collect_source_ids(item))
    elif isinstance(value, list):
        for item in value:
            result.update(collect_source_ids(item))
    return result


def validate_openapi_shape(report: ValidationReport) -> None:
    path = ROOT / "specs" / "openapi.yaml"
    data = load_yaml(path)
    if data.get("openapi") != "3.1.0":
        report.fail("OpenAPI 版本应为 3.1.0")
    paths = data.get("paths", {})
    required_paths = {
        "/articles/{articleId}",
        "/reading-sessions/{sessionId}/interactions",
        "/interactions/{interactionId}/events",
        "/feedback",
        "/admin/articles/{articleId}/releases",
    }
    missing = required_paths - set(paths)
    if missing:
        report.fail(f"OpenAPI 缺少核心路径: {sorted(missing)}")
    else:
        report.ok("OpenAPI 包含阅读、交互、SSE、反馈与发布核心路径")


def validate_prompt_workflow_refs(report: ValidationReport) -> None:
    prompts_doc = load_yaml(ROOT / "specs" / "prompts.yaml")
    workflow_doc = load_yaml(ROOT / "specs" / "reading-workflow.yaml")
    prompt_versions = {
        f"{name}@{spec['version']}"
        for name, spec in prompts_doc.get("prompts", {}).items()
        if isinstance(spec, dict) and "version" in spec
    }
    refs: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "prompt" and isinstance(item, str):
                    refs.add(item)
                elif key == "prompt_map" and isinstance(item, dict):
                    refs.update(str(x) for x in item.values())
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(workflow_doc)
    missing = refs - prompt_versions
    if missing:
        report.fail(f"Workflow 引用不存在 Prompt 版本: {sorted(missing)}")
    else:
        report.ok(f"Workflow 引用的 Prompt 版本均存在（{len(refs)} 个）")


def validate_starter(report: ValidationReport, run_pytest: bool) -> None:
    py_files = sorted(path for path in (ROOT / "starter" / "backend").rglob("*.py") if included_file(path))
    compile_errors = []
    for path in py_files:
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # noqa: BLE001
            compile_errors.append(f"{path.relative_to(ROOT)}: {exc}")
    if compile_errors:
        report.fail("Starter Python 编译失败: " + "; ".join(compile_errors))
    else:
        report.ok(f"Starter Python 编译通过（{len(py_files)} 个文件）")

    if not run_pytest:
        report.warn("跳过 starter pytest（使用 --skip-pytest）")
        return

    env = os.environ.copy()
    backend = ROOT / "starter" / "backend"
    env["PYTHONPATH"] = str(backend) + os.pathsep + env.get("PYTHONPATH", "")
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(backend / "tests")],
        cwd=backend,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if process.returncode != 0:
        output = (process.stdout + "\n" + process.stderr).strip()
        report.fail(f"Starter pytest 失败:\n{output}")
    else:
        summary = process.stdout.strip().splitlines()[-1] if process.stdout.strip() else "passed"
        report.ok(f"Starter smoke test 通过（{summary}）")


def validate_hash_manifest(report: ValidationReport) -> None:
    manifest_path = ROOT / "MANIFEST.sha256"
    if not manifest_path.exists():
        report.warn("MANIFEST.sha256 尚未生成；打包前运行 tools/generate_manifest.py")
        return
    mismatches: list[str] = []
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        if not path.is_file():
            mismatches.append(f"missing:{relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append(f"hash:{relative}")
    if mismatches:
        report.fail("MANIFEST 完整性失败: " + ", ".join(mismatches[:20]))
    else:
        report.ok("MANIFEST.sha256 完整性通过")


def write_markdown_report(report: ValidationReport) -> None:
    path = ROOT / "PACKAGE_VALIDATION_REPORT.md"
    lines = [
        "# 资料包校验报告",
        "",
        f"结论：{'通过' if report.success else '失败'}",
        "",
        "## 通过项",
        "",
    ]
    lines.extend(f"- ✅ {item}" for item in report.passed)
    lines.extend(["", "## 警告", ""])
    lines.extend(f"- ⚠️ {item}" for item in report.warnings)
    if not report.warnings:
        lines.append("- 无")
    lines.extend(["", "## 错误", ""])
    lines.extend(f"- ❌ {item}" for item in report.errors)
    if not report.errors:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "该报告验证资料包结构、规范示例、核心业务不变量和 Starter smoke test；不替代真实文章的历史内容审核、版权审核、Prompt 人工评测与生产压测。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def print_report(report: ValidationReport) -> None:
    for item in report.passed:
        print(f"[PASS] {item}")
    for item in report.warnings:
        print(f"[WARN] {item}")
    for item in report.errors:
        print(f"[FAIL] {item}", file=sys.stderr)
    print(
        f"\nSummary: passed={len(report.passed)} warnings={len(report.warnings)} errors={len(report.errors)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--skip-manifest", action="store_true")
    args = parser.parse_args()

    report = ValidationReport()
    validate_required_files(report)
    validate_parsing(report)
    validate_schema_files(report)
    validate_local_refs(report)
    validate_examples(report)
    validate_cross_object_invariants(report)
    validate_openapi_shape(report)
    validate_prompt_workflow_refs(report)
    validate_starter(report, run_pytest=not args.skip_pytest)
    if not args.skip_manifest:
        validate_hash_manifest(report)
    write_markdown_report(report)
    print_report(report)
    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
