#!/usr/bin/env python3
"""Find, review, approve, and download licensed animal images."""

from __future__ import annotations

import argparse
import csv
import html
import json
import mimetypes
import re
import ssl
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
from collections import OrderedDict
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
ANIMALS_JSON = SITE_ROOT / "data" / "animals.json"
MANIFEST_PATH = SITE_ROOT / "data" / "animal_image_manifest.json"
REVIEW_ROOT = SITE_ROOT / ".image-review"
CACHE_ROOT = SITE_ROOT / ".image-cache"
ANIMAL_ASSET_DIR = SITE_ROOT / "assets" / "animals"

ALLOWED_LICENSE_PATTERNS = [
    "cc0",
    "public domain",
    "publicdomain",
    "pd",
    "pdm",
    "cc by",
    "cc-by",
    "cc-by-sa",
    "cc by-sa",
    "cc by sa",
]

BLOCKED_LICENSE_PATTERNS = [
    "-nc",
    " nc",
    "noncommercial",
    "-nd",
    " nd",
    "no derivatives",
    "all rights reserved",
]

USER_AGENT = "DesignAZooStudentSite/1.0 (educational image review pipeline)"


def ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi  # type: ignore
    except ImportError:
        return None
    return ssl.create_default_context(cafile=certifi.where())


SSL_CONTEXT = ssl_context()


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "animal"


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return html.unescape(value).strip()


def request_json(url: str, *, timeout: int = 25) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8"))


def request_bytes(url: str, *, timeout: int = 45) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return response.read(), response.headers.get("Content-Type", "")


def read_animals() -> OrderedDict[str, dict]:
    animals = json.loads(ANIMALS_JSON.read_text(encoding="utf-8"))
    unique: OrderedDict[str, dict] = OrderedDict()
    for row in animals:
        unique.setdefault(row["animal_name"], row)
    return unique


def google_search_url(query: str) -> str:
    params = urllib.parse.urlencode({"tbm": "isch", "q": f"{query} Creative Commons"})
    return f"https://www.google.com/search?{params}"


def default_record(row: dict) -> dict:
    scientific_name = row.get("scientific_name", "")
    manual_review = scientific_name == "Not specified"
    query_parts = [row["animal_name"]]
    if scientific_name and scientific_name != "Not specified":
        query_parts.append(scientific_name)
    query = " ".join(query_parts)
    return {
        "animal_name": row["animal_name"],
        "scientific_name": scientific_name,
        "image_path": "",
        "alt_text": f"{row['animal_name']} photo",
        "credit": "",
        "source_url": "",
        "license_name": "",
        "license_url": "",
        "provider": "",
        "review_status": "pending",
        "notes": "Manual review required before approval." if manual_review else "",
        "manual_review_required": manual_review,
        "google_search_url": google_search_url(query),
        "candidates": [],
        "selected_candidate_index": None,
        "batch": "",
        "updated_at": "",
    }


def read_manifest() -> dict[str, dict]:
    if not MANIFEST_PATH.exists():
        return {}
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise SystemExit("Manifest must be an object keyed by animal name")
    return manifest


def write_manifest(manifest: dict[str, dict]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def license_allowed(license_name: str, license_url: str = "") -> bool:
    text = f"{license_name} {license_url}".lower()
    if any(pattern in text for pattern in BLOCKED_LICENSE_PATTERNS):
        return False
    return any(pattern in text for pattern in ALLOWED_LICENSE_PATTERNS)


def init_manifest() -> dict[str, dict]:
    unique = read_animals()
    manifest = read_manifest()
    new_manifest: dict[str, dict] = {}
    for animal_name, row in unique.items():
        record = default_record(row)
        if animal_name in manifest:
            record.update(manifest[animal_name])
            record["animal_name"] = animal_name
            record["scientific_name"] = row.get("scientific_name", "")
            record.setdefault("google_search_url", google_search_url(animal_name))
            record.setdefault("manual_review_required", row.get("scientific_name") == "Not specified")
            record.setdefault("candidates", [])
        new_manifest[animal_name] = record
    write_manifest(new_manifest)
    return new_manifest


def commons_candidates(query: str, limit: int = 6) -> list[dict]:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime|size",
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    data = request_json(url)
    pages = data.get("query", {}).get("pages", {})
    candidates: list[dict] = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        metadata = info.get("extmetadata", {})
        license_name = clean_html(metadata.get("LicenseShortName", {}).get("value", ""))
        license_url = clean_html(metadata.get("LicenseUrl", {}).get("value", ""))
        if not license_allowed(license_name, license_url):
            continue
        image_url = info.get("url", "")
        source_url = info.get("descriptionurl", "")
        artist = clean_html(metadata.get("Artist", {}).get("value", ""))
        credit = clean_html(metadata.get("Credit", {}).get("value", ""))
        author = artist or credit or "Wikimedia Commons contributor"
        candidates.append(
            {
                "provider": "Wikimedia Commons",
                "title": page.get("title", "").replace("File:", ""),
                "image_url": image_url,
                "thumbnail_url": image_url,
                "source_url": source_url,
                "credit": author,
                "license_name": license_name,
                "license_url": license_url,
                "width": info.get("width"),
                "height": info.get("height"),
            }
        )
    return candidates


def inaturalist_candidates(query: str, limit: int = 6) -> list[dict]:
    params = {
        "taxon_name": query,
        "photos": "true",
        "quality_grade": "research",
        "photo_license": "CC0,CC-BY,CC-BY-SA",
        "per_page": str(limit),
        "order_by": "votes",
        "order": "desc",
    }
    url = "https://api.inaturalist.org/v1/observations?" + urllib.parse.urlencode(params)
    data = request_json(url)
    candidates: list[dict] = []
    for observation in data.get("results", []):
        for photo in observation.get("photos", []):
            license_name = (photo.get("license_code") or "").upper()
            if license_name.startswith("CC-"):
                license_display = license_name.replace("-", " ")
            elif license_name == "CC0":
                license_display = "CC0"
            else:
                license_display = license_name
            if not license_allowed(license_display):
                continue
            image_url = (photo.get("url") or "").replace("square.", "large.")
            attribution = photo.get("attribution") or observation.get("user", {}).get("login") or "iNaturalist contributor"
            source_url = observation.get("uri") or f"https://www.inaturalist.org/observations/{observation.get('id')}"
            candidates.append(
                {
                    "provider": "iNaturalist",
                    "title": observation.get("taxon", {}).get("preferred_common_name") or query,
                    "image_url": image_url,
                    "thumbnail_url": photo.get("url") or image_url,
                    "source_url": source_url,
                    "credit": attribution,
                    "license_name": license_display,
                    "license_url": license_url_for(license_name),
                    "width": None,
                    "height": None,
                }
            )
            break
        if len(candidates) >= limit:
            break
    return candidates


def license_url_for(license_name: str) -> str:
    if license_name == "CC0":
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    if license_name.startswith("CC-"):
        code = license_name.replace("CC-", "").lower()
        return f"https://creativecommons.org/licenses/{code}/4.0/"
    return ""


def candidate_queries(record: dict) -> list[str]:
    queries = []
    scientific = record.get("scientific_name", "")
    if scientific and scientific != "Not specified":
        queries.append(scientific)
    queries.append(record["animal_name"])
    return list(dict.fromkeys(queries))


def find_one_record(record: dict) -> list[dict]:
    candidates: list[dict] = []
    seen = set()
    for query in candidate_queries(record):
        for finder in (commons_candidates, inaturalist_candidates):
            try:
                found = finder(query)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                record["notes"] = f"{record.get('notes', '')} {finder.__name__} failed for {query}: {error}".strip()
                found = []
            for candidate in found:
                key = candidate.get("image_url") or candidate.get("source_url")
                if key and key not in seen:
                    seen.add(key)
                    candidate["query"] = query
                    candidates.append(candidate)
        if candidates:
            break
    return candidates[:8]


def find_candidates(limit: int, batch: str, offset: int = 0, pause: float = 0.25) -> dict[str, dict]:
    manifest = init_manifest()
    eligible = [
        name
        for name, record in manifest.items()
        if record.get("review_status") in {"pending", "candidate", "needs_manual"} and not record.get("image_path")
    ]
    selected = eligible[offset : offset + limit]
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    for index, animal_name in enumerate(selected, start=1):
        record = manifest[animal_name]
        print(f"[{index}/{len(selected)}] finding candidates for {animal_name}")
        candidates = find_one_record(record)
        record["candidates"] = candidates
        record["batch"] = batch
        record["updated_at"] = now
        if candidates:
            record["review_status"] = "candidate"
            if record.get("manual_review_required"):
                record["notes"] = "Manual review required before approval because scientific name is not specified."
        else:
            record["review_status"] = "needs_manual"
            record["notes"] = "No licensed API candidate found. Use Google manual fallback and confirm license on the original host."
        time.sleep(pause)
    write_manifest(manifest)
    return {name: manifest[name] for name in selected}


def render_review(batch: str) -> Path:
    manifest = read_manifest()
    rows = [record for record in manifest.values() if record.get("batch") == batch]
    if not rows:
        raise SystemExit(f"No manifest records found for batch {batch}")

    review_dir = REVIEW_ROOT / batch
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "candidates.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cards = []
    for record in rows:
        candidate_html = []
        for index, candidate in enumerate(record.get("candidates", [])):
            candidate_html.append(
                f"""
                <article class="candidate">
                  <img src="{html.escape(candidate.get('thumbnail_url') or candidate.get('image_url') or '')}" alt="">
                  <div>
                    <h3>{html.escape(candidate.get('title') or 'Candidate image')}</h3>
                    <p>{html.escape(candidate.get('provider') or '')} - {html.escape(candidate.get('license_name') or '')}</p>
                    <p>{html.escape(candidate.get('credit') or '')}</p>
                    <a href="{html.escape(candidate.get('source_url') or '')}" target="_blank" rel="noopener noreferrer">Source</a>
                    <button type="button" data-animal="{html.escape(record['animal_name'])}" data-index="{index}">Approve this image</button>
                  </div>
                </article>
                """
            )
        if not candidate_html:
            candidate_html.append(
                f"""
                <article class="candidate empty">
                  <div>
                    <h3>No API candidate found</h3>
                    <a href="{html.escape(record.get('google_search_url') or '')}" target="_blank" rel="noopener noreferrer">Open Google manual fallback</a>
                    <p>Confirm license on the original host before approval.</p>
                  </div>
                </article>
                """
            )
        cards.append(
            f"""
            <section class="animal">
              <header>
                <h2>{html.escape(record['animal_name'])}</h2>
                <p><em>{html.escape(record.get('scientific_name') or '')}</em></p>
                <p>Status: {html.escape(record.get('review_status') or '')}</p>
                <button class="reject" type="button" data-animal="{html.escape(record['animal_name'])}">Reject all candidates</button>
              </header>
              <div class="candidates">{''.join(candidate_html)}</div>
            </section>
            """
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Animal Image Review - {html.escape(batch)}</title>
  <style>
    body {{ margin: 0; padding: 22px; font-family: Arial, sans-serif; background: #f5f8f4; color: #182422; }}
    header.page {{ max-width: 1180px; margin: 0 auto 18px; }}
    .animal {{ max-width: 1180px; margin: 0 auto 18px; padding: 16px; background: white; border: 1px solid #d7dfda; border-radius: 8px; }}
    .animal > header {{ display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; align-items: center; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    .candidates {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }}
    .candidate {{ overflow: hidden; border: 1px solid #d7dfda; border-radius: 8px; background: #fbfdfb; }}
    .candidate img {{ width: 100%; height: 180px; object-fit: cover; display: block; background: #dcefed; }}
    .candidate div {{ padding: 12px; }}
    button {{ min-height: 38px; padding: 8px 12px; border-radius: 8px; border: 1px solid #0f766e; background: #0f766e; color: white; font-weight: 700; cursor: pointer; }}
    button.reject {{ background: #fff8e8; color: #6c3f09; border-color: #d8951b; }}
    textarea {{ width: 100%; min-height: 180px; margin-top: 16px; }}
  </style>
</head>
<body>
  <header class="page">
    <h1>Animal Image Review: {html.escape(batch)}</h1>
    <p>Approve only images with a suitable animal match and acceptable license metadata. Save exported decisions as <code>.image-review/{html.escape(batch)}/decisions.json</code>.</p>
    <button id="export" type="button">Export Decisions</button>
    <textarea id="output" aria-label="Exported decisions"></textarea>
  </header>
  {''.join(cards)}
  <script>
    const decisions = {{}};
    document.addEventListener('click', (event) => {{
      const button = event.target.closest('button');
      if (!button) return;
      const animal = button.dataset.animal;
      if (button.id === 'export') {{
        document.querySelector('#output').value = JSON.stringify(decisions, null, 2);
        return;
      }}
      if (!animal) return;
      if (button.classList.contains('reject')) {{
        decisions[animal] = {{ decision: 'reject' }};
        button.textContent = 'Rejected';
        return;
      }}
      decisions[animal] = {{ decision: 'approve', candidate_index: Number(button.dataset.index) }};
      button.textContent = 'Approved';
    }});
  </script>
</body>
</html>
"""
    (review_dir / "index.html").write_text(html_doc, encoding="utf-8")
    return review_dir / "index.html"


def apply_decisions(path: Path) -> None:
    manifest = read_manifest()
    decisions = json.loads(path.read_text(encoding="utf-8"))
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    for animal_name, decision in decisions.items():
        if animal_name not in manifest:
            raise SystemExit(f"Unknown animal in decisions: {animal_name}")
        record = manifest[animal_name]
        if decision.get("decision") == "reject":
            record["review_status"] = "rejected"
            record["notes"] = "Rejected during batch review."
            record["selected_candidate_index"] = None
        elif decision.get("decision") == "approve":
            index = int(decision.get("candidate_index", -1))
            candidates = record.get("candidates") or []
            if index < 0 or index >= len(candidates):
                raise SystemExit(f"Invalid candidate index for {animal_name}: {index}")
            candidate = candidates[index]
            if not license_allowed(candidate.get("license_name", ""), candidate.get("license_url", "")):
                raise SystemExit(f"Disallowed license for {animal_name}: {candidate.get('license_name')}")
            record["review_status"] = "approved"
            record["selected_candidate_index"] = index
            record["alt_text"] = f"{animal_name} photo"
            record["credit"] = candidate.get("credit", "")
            record["source_url"] = candidate.get("source_url", "")
            record["license_name"] = candidate.get("license_name", "")
            record["license_url"] = candidate.get("license_url", "")
            record["provider"] = candidate.get("provider", "")
            record["notes"] = "Approved in batch review."
        else:
            raise SystemExit(f"Unknown decision for {animal_name}: {decision}")
        record["updated_at"] = now
    write_manifest(manifest)


def convert_to_webp(source_path: Path, target_path: Path) -> None:
    try:
        from PIL import Image  # type: ignore
    except ImportError as error:
        raise SystemExit("Pillow is required for image conversion. Install it with: python3 -m pip install Pillow") from error

    with Image.open(source_path) as image:
        image.thumbnail((900, 700))
        rgb = image.convert("RGB")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(target_path, "WEBP", quality=82, method=6)


def download_approved(limit: int | None = None) -> int:
    manifest = read_manifest()
    approved = [
        record
        for record in manifest.values()
        if record.get("review_status") == "approved" and not record.get("image_path")
    ]
    if limit is not None:
        approved = approved[:limit]
    count = 0
    for record in approved:
        index = record.get("selected_candidate_index")
        candidates = record.get("candidates") or []
        if index is None or int(index) >= len(candidates):
            raise SystemExit(f"Approved record has no selected candidate: {record['animal_name']}")
        candidate = candidates[int(index)]
        image_url = candidate.get("image_url")
        if not image_url:
            raise SystemExit(f"Approved candidate has no image_url: {record['animal_name']}")
        print(f"Downloading {record['animal_name']}")
        image_bytes, content_type = request_bytes(image_url)
        suffix = mimetypes.guess_extension(content_type.split(";")[0]) or ".img"
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=suffix, dir=CACHE_ROOT, delete=False) as temp:
            temp.write(image_bytes)
            temp_path = Path(temp.name)
        target = ANIMAL_ASSET_DIR / f"{slugify(record['animal_name'])}.webp"
        convert_to_webp(temp_path, target)
        temp_path.unlink(missing_ok=True)
        record["image_path"] = str(target.relative_to(SITE_ROOT))
        count += 1
    write_manifest(manifest)
    return count


def export_worklist(path: Path) -> None:
    unique = read_animals()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["animal_name", "scientific_name", "primary_habitat"])
        writer.writeheader()
        for row in unique.values():
            writer.writerow(
                {
                    "animal_name": row["animal_name"],
                    "scientific_name": row["scientific_name"],
                    "primary_habitat": row["primary_habitat"],
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-manifest")

    find_parser = subparsers.add_parser("find-candidates")
    find_parser.add_argument("--limit", type=int, default=25)
    find_parser.add_argument("--offset", type=int, default=0)
    find_parser.add_argument("--batch", default="pilot_001")

    review_parser = subparsers.add_parser("render-review")
    review_parser.add_argument("--batch", default="pilot_001")

    apply_parser = subparsers.add_parser("apply-decisions")
    apply_parser.add_argument("--file", required=True)

    download_parser = subparsers.add_parser("download-approved")
    download_parser.add_argument("--limit", type=int)

    export_parser = subparsers.add_parser("export-worklist")
    export_parser.add_argument("--output", default="data/animal_image_worklist.csv")

    args = parser.parse_args()

    if args.command == "init-manifest":
        manifest = init_manifest()
        print(f"Initialized manifest for {len(manifest):,} unique animals at {MANIFEST_PATH.relative_to(SITE_ROOT)}")
    elif args.command == "find-candidates":
        selected = find_candidates(args.limit, args.batch, args.offset)
        with_candidates = sum(1 for record in selected.values() if record.get("candidates"))
        print(f"Updated {len(selected):,} records; {with_candidates:,} have licensed API candidates.")
    elif args.command == "render-review":
        path = render_review(args.batch)
        print(f"Review gallery written to {path}")
    elif args.command == "apply-decisions":
        apply_decisions(Path(args.file))
        print("Applied review decisions.")
    elif args.command == "download-approved":
        count = download_approved(args.limit)
        print(f"Downloaded {count:,} approved images.")
    elif args.command == "export-worklist":
        output = SITE_ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        export_worklist(output)
        print(f"Worklist exported to {output.relative_to(SITE_ROOT)}")


if __name__ == "__main__":
    main()
