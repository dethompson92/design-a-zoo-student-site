#!/usr/bin/env python3
"""Audit Design a Zoo project files for student-safe interactive tool ideas."""

from __future__ import annotations

import csv
import html
import json
import re
import subprocess
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree


SITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SITE_ROOT.parent
OUTPUT_ROOT = SITE_ROOT / ".image-review" / "project-tool-audit"
REPORT_PATH = SITE_ROOT / "docs" / "PROJECT_TOOL_AUDIT.md"

TEXT_EXTENSIONS = {".csv", ".docx", ".html", ".json", ".md", ".pdf", ".txt", ".xlsx"}
PRIVATE_TOP_LEVEL = {"Grade 7"}
SKIP_PARTS = {".git", ".image-cache", ".image-review", "__pycache__"}

TOOL_KEYWORDS = {
    "probability_simulation": [
        "probability",
        "simulation",
        "sample space",
        "experimental",
        "theoretical",
        "random",
        "trials",
        "chance",
    ],
    "survey_data": [
        "survey",
        "sample",
        "sampling",
        "relative frequency",
        "percent",
        "percentage",
        "bar graph",
        "data display",
        "claim",
        "limitation",
    ],
    "budget_revenue": [
        "budget",
        "revenue",
        "profit",
        "loss",
        "swagg",
        "equation",
        "cost",
        "grant",
        "fee",
        "discount",
    ],
    "design_constraints": [
        "area",
        "perimeter",
        "scale",
        "scale drawing",
        "dimension",
        "enclosure",
        "minimum group",
        "family group",
        "space",
        "model",
    ],
}


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def should_skip(path: Path) -> bool:
    parts = path.relative_to(PROJECT_ROOT).parts
    return any(part in SKIP_PARTS for part in parts)


def classify_path(path: Path) -> tuple[str, bool]:
    parts = path.relative_to(PROJECT_ROOT).parts
    lower = rel(path).lower()
    if parts and parts[0] in PRIVATE_TOP_LEVEL:
        return "private student/accommodation record; content not extracted", False
    if parts and parts[0] == "design-a-zoo-student-site":
        return "public site implementation", False
    if any(token in lower for token in ["answer_key", "answer key", "teacher", "confidential", "scoring_guide"]):
        return "teacher-only local source; do not publish directly", True
    if "student" in lower or "workbook" in lower or "packet" in lower:
        return "student-safe source candidate", True
    if "zoo_animals_student_database_final.csv" in lower:
        return "public data source", True
    if "geometry_worksheets" in lower or "prompt" in lower:
        return "reference source", True
    return "local reference source", True


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(value))


def extract_docx(path: Path) -> str:
    pieces: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                try:
                    root = ElementTree.fromstring(archive.read(name))
                except ElementTree.ParseError:
                    continue
                for node in root.iter():
                    if node.tag.endswith("}t") and node.text:
                        pieces.append(node.text)
    return " ".join(pieces)


def extract_xlsx(path: Path) -> str:
    pieces: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith("xl/sharedStrings") or name.startswith("xl/worksheets/"):
                try:
                    root = ElementTree.fromstring(archive.read(name))
                except ElementTree.ParseError:
                    continue
                for node in root.iter():
                    if node.text and len(node.text.strip()) > 1:
                        pieces.append(node.text.strip())
    return " ".join(pieces)


def extract_pdf(path: Path) -> str:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "out.txt"
            subprocess.run(
                ["pdftotext", str(path), str(output)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            return output.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def extract_csv(path: Path) -> str:
    pieces: list[str] = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        reader = csv.reader(handle)
        for index, row in enumerate(reader):
            pieces.append(" ".join(row))
            if index > 200:
                pieces.append("[csv truncated after 200 rows for audit]")
                break
    return " ".join(pieces)


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".docx":
            return extract_docx(path), "docx text"
        if suffix == ".xlsx":
            return extract_xlsx(path), "xlsx text"
        if suffix == ".pdf":
            text = extract_pdf(path)
            return text, "pdf text" if text else "pdf filename only"
        if suffix == ".csv":
            return extract_csv(path), "csv text"
        if suffix in {".md", ".txt", ".html", ".json"}:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            return strip_tags(raw) if suffix == ".html" else raw, f"{suffix[1:]} text"
    except Exception as exc:  # noqa: BLE001 - audit should continue
        return "", f"unreadable: {exc}"
    return "", "unsupported"


def keyword_hits(text: str) -> dict[str, int]:
    lowered = text.lower()
    hits = {}
    for category, words in TOOL_KEYWORDS.items():
        count = 0
        for word in words:
            count += lowered.count(word)
        if count:
            hits[category] = count
    return hits


def budget_mentions(text: str) -> Counter:
    counts: Counter = Counter()
    for match in re.findall(r"\$?\b[0-9],[0-9]{3},[0-9]{3}\b", text):
        counts[match.replace("$", "")] += 1
    return counts


def run_audit() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    category_files: dict[str, set[str]] = defaultdict(set)
    status_counts: Counter = Counter()
    extension_counts: Counter = Counter()
    budget_counts: Counter = Counter()

    for path in sorted(PROJECT_ROOT.rglob("*"), key=lambda item: rel(item).lower() if item.is_file() else ""):
        if not path.is_file() or should_skip(path):
            continue
        extension_counts[path.suffix.lower() or "[none]"] += 1
        public_status, extract_allowed = classify_path(path)
        status_counts[public_status] += 1
        record = {
            "path": rel(path),
            "extension": path.suffix.lower() or "[none]",
            "size_bytes": path.stat().st_size,
            "public_status": public_status,
            "scan_status": "not extracted",
            "tool_hits": {},
        }
        if path.suffix.lower() in TEXT_EXTENSIONS and extract_allowed:
            text, scan_status = extract_text(path)
            record["scan_status"] = scan_status
            hits = keyword_hits(text)
            record["tool_hits"] = hits
            budget_counts.update(budget_mentions(text))
            if "teacher-only" not in public_status:
                for category in hits:
                    category_files[category].add(record["path"])
        records.append(record)

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(PROJECT_ROOT),
        "files_scanned": len(records),
        "extension_counts": dict(extension_counts),
        "public_status_counts": dict(status_counts),
        "student_safe_tool_category_file_counts": {key: len(value) for key, value in sorted(category_files.items())},
        "budget_mentions": dict(budget_counts),
        "records": records,
    }
    (OUTPUT_ROOT / "project_tool_inventory.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(markdown_report(summary, category_files), encoding="utf-8")
    print(f"Audited {len(records):,} files")
    print(f"Wrote {REPORT_PATH.relative_to(SITE_ROOT)}")


def markdown_report(summary: dict, category_files: dict[str, set[str]]) -> str:
    lines = [
        "# Project Tool Audit",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        "- The project materials support a student-facing interactive Zoo Lab: probability simulation, survey/data displays, budget/revenue modeling, and enclosure design checks.",
        "- Teacher-only guides, answer keys, confidential accommodation files, and student snapshot records should stay local-only; the file lists below use student-safe or reference sources only.",
        "- The current public site budget remains `$2,500,000`; older packet/source references to `$2,000,000` should be treated as historical unless the classroom directions are changed.",
        "- The strongest implementation pattern is a dependency-free static tool page, matching the existing public site and the referenced probability-lab style.",
        "",
        "## Files Scanned",
        "",
        f"- Total files inventoried: {summary['files_scanned']}",
    ]
    for status, count in sorted(summary["public_status_counts"].items()):
        lines.append(f"- {status}: {count}")

    lines.extend(["", "## Tool Opportunities Found", ""])
    opportunity_labels = {
        "probability_simulation": "Probability simulation",
        "survey_data": "Visitor survey and data displays",
        "budget_revenue": "Budget, percent events, revenue, and SWAGG equations",
        "design_constraints": "Enclosure area, scale, dimensions, and design constraints",
    }
    for category, label in opportunity_labels.items():
        files = sorted(category_files.get(category, []))
        lines.append(f"- {label}: found in {len(files)} project files.")
        for file_path in files[:8]:
            lines.append(f"  - `{file_path}`")

    lines.extend(
        [
            "",
            "## Student-Safe Build Targets",
            "",
            "- `Zoo Probability Lab`: run at least 30 trials, show sample space, experimental probability, theoretical probability for weighted models, and a claim/limitation summary.",
            "- `Visitor Survey + Data Displays`: enter or load survey counts, calculate percents and relative frequencies, and generate a bar-style display with a sampling limitation.",
            "- `Budget + Revenue Studio`: select animals from the verified public database, enforce minimum group quantities, apply percent events, evaluate SWAGG equations, and track the `$2,500,000` budget.",
            "- `Enclosure Design Check`: compare student dimensions against required classroom planning area using the first-animal plus additional-animal space formula.",
            "",
            "## Public-Safety Rules",
            "",
            "- Publish only student-facing summaries and tools, not answer keys or teacher scoring guidance.",
            "- Do not publish Grade 7 snapshot files or confidential accommodation materials.",
            "- Keep image provenance and license checks separate from tool content.",
            "- Treat the public animal database as the source of truth for animal names, spaces, costs, habitats, regions, SWAGG equations, and research links.",
            "",
            "## Local Audit Artifact",
            "",
            "- `.image-review/project-tool-audit/project_tool_inventory.json` contains the machine-readable file inventory and hit counts. It stays local-only.",
        ]
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    run_audit()
