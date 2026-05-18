#!/usr/bin/env python3
"""Audit local project folders for usable image and reference assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageStat


SITE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SITE_ROOT.parent
OUTPUT_ROOT = SITE_ROOT / ".image-review" / "local-source-audit"
REPORT_PATH = SITE_ROOT / "docs" / "LOCAL_SOURCE_AUDIT.md"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".csv", ".docx", ".html", ".json", ".md", ".pdf", ".txt", ".xlsx"}

SKIP_TOP_LEVEL = {"design-a-zoo-student-site"}
SKIP_PARTS = {".git", ".image-cache", ".image-review", "__pycache__"}


def rel_path(path: Path) -> str:
    return path.relative_to(WORKSPACE_ROOT).as_posix()


def should_skip(path: Path) -> bool:
    parts = path.relative_to(WORKSPACE_ROOT).parts
    if parts and parts[0] in SKIP_TOP_LEVEL:
        return True
    return any(part in SKIP_PARTS for part in parts)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dhash(image: Image.Image) -> str:
    gray = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    bits = []
    for row in range(8):
        offset = row * 9
        for col in range(8):
            bits.append(1 if pixels[offset + col] > pixels[offset + col + 1] else 0)
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return f"{value:016x}"


def classify_path(path: Path) -> tuple[str, str, str]:
    rel_lower = rel_path(path).lower()
    name_lower = path.name.lower()

    if "wild_ecosystem_habitats_collection" in rel_lower:
        return (
            "habitat asset",
            "already-used habitat image",
            "Keep as habitat imagery; these have already been copied into the public site.",
        )
    if "zoo_geometry_worksheets" in rel_lower:
        return (
            "worksheet image",
            "reference only",
            "Useful for a separate geometry worksheet resource, not for animal photo cards.",
        )
    if "zoo_design_studio_project" in rel_lower and "teacher_guide" in rel_lower:
        return (
            "teacher guide page",
            "do not publish",
            "Teacher-guide and answer material should stay local-only unless a student-safe extract is created.",
        )
    if "zoo_design_studio_project" in rel_lower and "student_packet" in rel_lower:
        return (
            "student packet page",
            "reference only",
            "Useful for a future student resources page, but not for animal photo cards.",
        )
    if "archive_20260518" in rel_lower:
        return (
            "archived packet page",
            "reference only",
            "Useful as backup/reference material; prefer current student packet files for public resources.",
        )
    if "googledocs_classwork_teacher_key" in rel_lower:
        return (
            "classwork document",
            "reference only",
            "Useful for classwork context; teacher-key material should stay out of the public repo.",
        )
    if "image_generator_master_prompts" in rel_lower:
        return (
            "prompt/reference file",
            "reference only",
            "Useful for future image-generation prompts, not a publishable animal image source.",
        )
    if "exhibition_capstone_project_packet" in rel_lower:
        return (
            "capstone packet source",
            "reference only",
            "Useful source context; publish only student-facing, non-answer materials.",
        )
    if "untitled folder" in rel_lower:
        if "media_and_images" in rel_lower or name_lower.startswith("image_"):
            return (
                "local export image",
                "hold for manual review",
                "Technically reviewable, but it needs owner/provenance confirmation before public use.",
            )
        return (
            "local export file",
            "reference only",
            "Conversation/export material can help reconstruct intent, but should not be published directly.",
        )
    if "animals/" in rel_lower:
        return (
            "polluted animal markdown source",
            "do not publish",
            "This folder was previously excluded because it contains generated clutter and non-student records.",
        )
    if rel_lower.startswith("assets/"):
        return (
            "legacy asset folder",
            "hold for manual review",
            "Potentially useful, but it needs the same provenance and quality checks as other local images.",
        )

    return (
        "workspace file",
        "reference only",
        "Keep as local context unless it has explicit classroom/public-site value.",
    )


def analyze_image(path: Path) -> dict:
    size_bytes = path.stat().st_size
    record = {
        "path": rel_path(path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": size_bytes,
        "format": "",
        "width": 0,
        "height": 0,
        "megapixels": 0.0,
        "aspect_ratio": 0.0,
        "mode": "",
        "has_alpha": False,
        "sha256": "",
        "dhash": "",
        "brightness": 0.0,
        "contrast": 0.0,
        "edge_detail": 0.0,
        "technical_status": "unreadable",
        "quality_flags": [],
        "source_category": "",
        "use_recommendation": "",
        "notes": "",
    }

    source_category, use_recommendation, notes = classify_path(path)
    record["source_category"] = source_category
    record["use_recommendation"] = use_recommendation
    record["notes"] = notes

    try:
        record["sha256"] = sha256_file(path)
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            record["format"] = image.format or ""
            record["width"] = width
            record["height"] = height
            record["megapixels"] = round((width * height) / 1_000_000, 3)
            record["aspect_ratio"] = round(width / height, 3) if height else 0
            record["mode"] = image.mode
            record["has_alpha"] = image.mode in {"RGBA", "LA"} or (
                image.mode == "P" and "transparency" in image.info
            )
            record["dhash"] = dhash(image)

            sample = ImageOps.grayscale(ImageOps.exif_transpose(image)).resize(
                (256, 256), Image.Resampling.LANCZOS
            )
            stats = ImageStat.Stat(sample)
            record["brightness"] = round(stats.mean[0], 2)
            record["contrast"] = round(stats.stddev[0], 2)
            edges = sample.filter(ImageFilter.FIND_EDGES)
            record["edge_detail"] = round(ImageStat.Stat(edges).stddev[0], 2)
    except Exception as exc:  # noqa: BLE001 - audit should keep going
        record["quality_flags"].append(f"unreadable: {exc}")
        return record

    flags: list[str] = []
    if record["width"] < 600 or record["height"] < 400:
        flags.append("below minimum card size")
    elif record["width"] < 900 or record["height"] < 600:
        flags.append("usable but low resolution")
    if record["aspect_ratio"] < 0.55 or record["aspect_ratio"] > 2.5:
        flags.append("extreme aspect ratio")
    if record["size_bytes"] < 20_000:
        flags.append("very small file")
    if record["size_bytes"] > 8_000_000:
        flags.append("large file; optimize before use")
    if record["brightness"] < 35:
        flags.append("very dark")
    if record["brightness"] > 225:
        flags.append("very bright")
    if record["contrast"] < 18:
        flags.append("low contrast")
    if record["edge_detail"] < 5:
        flags.append("low detail or flat graphic")

    record["quality_flags"] = flags
    blocking_flags = {
        "below minimum card size",
        "extreme aspect ratio",
        "very small file",
        "very dark",
        "very bright",
        "low contrast",
        "low detail or flat graphic",
    }
    record["technical_status"] = "reviewable" if not blocking_flags.intersection(flags) else "needs work"
    return record


def iter_workspace_files() -> list[Path]:
    files: list[Path] = []
    for path in WORKSPACE_ROOT.rglob("*"):
        if path.is_file() and not should_skip(path):
            files.append(path)
    return sorted(files, key=lambda item: rel_path(item).lower())


def summarize_non_images(files: list[Path]) -> dict:
    by_folder: dict[str, Counter] = defaultdict(Counter)
    notable: list[dict] = []
    for path in files:
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            continue
        ext = path.suffix.lower() or "[none]"
        if ext not in DOCUMENT_EXTENSIONS:
            continue
        folder = path.relative_to(WORKSPACE_ROOT).parts[0]
        by_folder[folder][ext] += 1
        source_category, use_recommendation, notes = classify_path(path)
        if path.name in {
            "zoo_animals_student_database_final.csv",
            "Design_a_Zoo_GoogleDocs_Student_Classwork_Workbook.pdf",
            "Design_a_Zoo_GoogleDocs_Answer_Key_and_Sample_Zoo.pdf",
            "Design_a_Zoo_Image_Generator_Master_Prompts_STUDENT.md",
            "Design_a_Zoo_Image_Generator_Master_Prompts_TEACHER.md",
            "Design_a_Zoo_Digital_Animal_Database.html",
        }:
            notable.append(
                {
                    "path": rel_path(path),
                    "source_category": source_category,
                    "use_recommendation": use_recommendation,
                    "notes": notes,
                }
            )
    return {
        "by_folder": {folder: dict(counter) for folder, counter in sorted(by_folder.items())},
        "notable": notable,
    }


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(records[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def make_contact_sheet(records: list[dict], output_path: Path, *, limit: int = 60) -> None:
    selected = [
        record
        for record in records
        if record["technical_status"] == "reviewable"
        and record["use_recommendation"] in {"hold for manual review", "reference only"}
    ][:limit]
    if not selected:
        return

    thumb_w, thumb_h = 220, 150
    label_h = 74
    pad = 12
    columns = 4
    rows = (len(selected) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (columns * (thumb_w + pad) + pad, rows * (thumb_h + label_h + pad) + pad),
        "white",
    )
    draw = ImageDraw.Draw(canvas)

    for index, record in enumerate(selected):
        x = pad + (index % columns) * (thumb_w + pad)
        y = pad + (index // columns) * (thumb_h + label_h + pad)
        image_path = WORKSPACE_ROOT / record["path"]
        try:
            with Image.open(image_path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                tx = x + (thumb_w - image.width) // 2
                ty = y + (thumb_h - image.height) // 2
                canvas.paste(image, (tx, ty))
        except Exception:
            draw.rectangle([x, y, x + thumb_w, y + thumb_h], outline="#cc0000", width=2)
            draw.text((x + 6, y + 6), "unreadable", fill="#cc0000")

        label = record["path"]
        if len(label) > 78:
            label = "..." + label[-75:]
        meta = f"{record['width']}x{record['height']} | {record['source_category']}"
        draw.rectangle([x, y + thumb_h + 4, x + thumb_w, y + thumb_h + label_h], fill="#f4f4f4")
        draw.text((x + 5, y + thumb_h + 8), label[:48], fill="#111111")
        draw.text((x + 5, y + thumb_h + 26), label[48:96], fill="#111111")
        draw.text((x + 5, y + thumb_h + 48), meta[:48], fill="#555555")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=88)


def duplicate_groups(records: list[dict], key: str) -> list[list[dict]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        value = record.get(key)
        if value:
            buckets[value].append(record)
    return [group for group in buckets.values() if len(group) > 1]


def markdown_report(summary: dict, image_records: list[dict], non_images: dict) -> str:
    source_counts = Counter(record["source_category"] for record in image_records)
    recommendation_counts = Counter(record["use_recommendation"] for record in image_records)
    technical_counts = Counter(record["technical_status"] for record in image_records)
    untitled = [record for record in image_records if record["path"].startswith("untitled folder/")]
    untitled_reviewable = [
        record
        for record in untitled
        if record["technical_status"] == "reviewable"
        and record["use_recommendation"] == "hold for manual review"
    ]

    lines = [
        "# Local Source Asset Audit",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        "- Do not publish any images from `untitled folder` directly into animal cards yet.",
        "- Many local exports are technically reviewable, but they do not carry the source URL, author, license name, or license URL required by the animal image pipeline.",
        "- Visual spot-checking shows the strongest `untitled folder` images are mostly worksheet pages, packet covers, trackers, rubrics, and planning sheets, not individual animal photos.",
        "- The folder is still useful: it contains image-generation exports and conversation context that can guide future classroom-resource visuals after provenance is confirmed.",
        "- The 100+ geometry worksheet images are useful for a separate classwork/worksheet resource page, not for the public animal-photo fields.",
        "- `Zoo/Zoo_Design_Studio_Project/Student_Packet/` has cleaner student packet page images that are better candidates for a future resources page than the repeated exports.",
        "- Teacher-key and answer materials should remain local-only.",
        "",
        "## Counts",
        "",
        f"- Workspace images scanned outside the public site repo: {len(image_records)}",
        f"- Images inside `untitled folder`: {len(untitled)}",
        f"- Technically reviewable `untitled folder` images needing manual provenance review: {len(untitled_reviewable)}",
        f"- Exact duplicate image groups: {summary['exact_duplicate_groups']}",
        f"- Near-duplicate perceptual groups: {summary['near_duplicate_groups']}",
        "",
        "## Technical Status",
        "",
    ]
    for name, count in sorted(technical_counts.items()):
        lines.append(f"- {name}: {count}")

    lines.extend(["", "## Source Categories", ""])
    for name, count in sorted(source_counts.items()):
        lines.append(f"- {name}: {count}")

    lines.extend(["", "## Use Recommendations", ""])
    for name, count in sorted(recommendation_counts.items()):
        lines.append(f"- {name}: {count}")

    lines.extend(
        [
            "",
            "## Useful Project Files Found",
            "",
            "- `Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package/zoo_animals_student_database_final.csv`: already the correct public source of truth.",
            "- `Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package/Design_a_Zoo_Digital_Animal_Database.html`: useful historical/reference copy, but the rebuilt static site should stay canonical.",
            "- `Design_a_Zoo_GoogleDocs_Classwork_Teacher_Key_Bundle/Design_a_Zoo_GoogleDocs_Student_Classwork_Workbook.pdf`: useful student-facing classwork reference if a future resources page is added.",
            "- `Design_a_Zoo_GoogleDocs_Classwork_Teacher_Key_Bundle/Design_a_Zoo_GoogleDocs_Answer_Key_and_Sample_Zoo.pdf`: teacher-only; do not publish.",
            "- `Design_a_Zoo_Image_Generator_Master_Prompts_Bundle/Design_a_Zoo_Image_Generator_Master_Prompts_STUDENT.md`: useful for a future student image-generation guide.",
            "- `Design_a_Zoo_Image_Generator_Master_Prompts_Bundle/Design_a_Zoo_Image_Generator_Master_Prompts_TEACHER.md`: teacher-only planning reference.",
            "- `Zoo/Zoo_Geometry_Worksheets_100_Images_Final_20260514_031256/`: useful as a separate worksheet/geometry resource set after student/teacher separation.",
            "- `Wild_Ecosystem_Habitats_Collection/`: already used for the 50 habitat images in the public site.",
            "",
            "## Local Audit Artifacts",
            "",
            "- `.image-review/local-source-audit/local_image_inventory.csv`: full image quality inventory.",
            "- `.image-review/local-source-audit/local_image_summary.json`: machine-readable counts and duplicate groups.",
            "- `.image-review/local-source-audit/local_image_candidates.json`: technically reviewable local exports that still require provenance/manual approval.",
            "- `.image-review/local-source-audit/contact_sheet_untitled_candidates.jpg`: visual sample sheet for reviewable local exports.",
            "- `.image-review/local-source-audit/contact_sheet_zoo_design_studio_export.jpg`: visual sample sheet for the larger Zoo Design Studio export.",
            "",
            "## Required Checks Before Using Any Local Image",
            "",
            "- Confirm ownership/provenance for the exact image file.",
            "- Record source, credit, license/usage permission, and reviewer decision in a manifest before publishing.",
            "- Reject worksheet screenshots, teacher-key pages, watermarked/stock-preview images, unclear rights, and images with text overlays that would confuse animal cards.",
            "- Optimize approved images to `.webp` and keep them under `assets/animals/` only after approval.",
        ]
    )

    if non_images["notable"]:
        lines.extend(["", "## Notable File Records", ""])
        for item in non_images["notable"]:
            lines.append(f"- `{item['path']}`: {item['use_recommendation']} - {item['notes']}")

    lines.append("")
    return "\n".join(lines)


def run_audit() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    files = iter_workspace_files()
    image_paths = [path for path in files if path.suffix.lower() in IMAGE_EXTENSIONS]
    image_records = [analyze_image(path) for path in image_paths]

    exact_groups = duplicate_groups(image_records, "sha256")
    near_groups = duplicate_groups(image_records, "dhash")
    non_images = summarize_non_images(files)

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workspace_root": str(WORKSPACE_ROOT),
        "images_scanned": len(image_records),
        "exact_duplicate_groups": len(exact_groups),
        "near_duplicate_groups": len(near_groups),
        "exact_duplicates": [[record["path"] for record in group] for group in exact_groups[:50]],
        "near_duplicates": [[record["path"] for record in group] for group in near_groups[:50]],
        "technical_status_counts": dict(Counter(record["technical_status"] for record in image_records)),
        "source_category_counts": dict(Counter(record["source_category"] for record in image_records)),
        "use_recommendation_counts": dict(Counter(record["use_recommendation"] for record in image_records)),
        "non_image_summary": non_images,
    }

    write_csv(image_records, OUTPUT_ROOT / "local_image_inventory.csv")
    (OUTPUT_ROOT / "local_image_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    local_candidates = [
        record
        for record in image_records
        if record["technical_status"] == "reviewable"
        and record["use_recommendation"] == "hold for manual review"
    ]
    (OUTPUT_ROOT / "local_image_candidates.json").write_text(
        json.dumps(local_candidates, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    untitled_records = [record for record in image_records if record["path"].startswith("untitled folder/")]
    make_contact_sheet(
        sorted(
            untitled_records,
            key=lambda record: (
                record["technical_status"] != "reviewable",
                record["use_recommendation"] != "hold for manual review",
                -record["megapixels"],
            ),
        ),
        OUTPUT_ROOT / "contact_sheet_untitled_candidates.jpg",
    )
    make_contact_sheet(
        sorted(
            image_records,
            key=lambda record: (
                record["technical_status"] != "reviewable",
                record["use_recommendation"] != "hold for manual review",
                -record["megapixels"],
            ),
        ),
        OUTPUT_ROOT / "contact_sheet_workspace_candidates.jpg",
    )

    studio_records = [
        record
        for record in image_records
        if "Teaching - 051426 - Zoo Design Studio project image generation request_export"
        in record["path"]
    ]
    make_contact_sheet(
        sorted(studio_records, key=lambda record: record["path"]),
        OUTPUT_ROOT / "contact_sheet_zoo_design_studio_export.jpg",
        limit=90,
    )

    REPORT_PATH.write_text(markdown_report(summary, image_records, non_images), encoding="utf-8")

    print(f"Scanned {len(image_records)} images")
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {OUTPUT_ROOT / 'local_image_inventory.csv'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit local Design a Zoo source folders.")
    parser.parse_args()
    run_audit()


if __name__ == "__main__":
    main()
