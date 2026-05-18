# Animal Image Pipeline

This workflow adds one approved image per unique animal name and reuses that image anywhere the animal appears in multiple habitats. The review manifest and candidate gallery are local-only; the public site only receives approved image paths and credits after review.

## Rules

- Do not scrape Google Images directly.
- Publish only images with confirmed source URL, credit, provider, license name, and license URL.
- Allowed default licenses are CC0, public domain, CC BY, and CC BY-SA.
- Do not publish noncommercial, no-derivatives, stock-preview, watermarked, unclear, or all-rights-reserved images.
- Animals with `scientific_name = "Not specified"` require manual review before approval.

## Commands

Initialize or refresh the manifest:

```bash
python3 scripts/animal_image_pipeline.py init-manifest
```

Audit local folders before considering locally generated or exported images:

```bash
python3 scripts/audit_local_sources.py
```

This writes a tracked summary to `docs/LOCAL_SOURCE_AUDIT.md` and keeps detailed inventories/contact sheets in `.image-review/local-source-audit/`.

Find the first 25 candidates:

```bash
python3 scripts/animal_image_pipeline.py find-candidates --limit 25 --batch pilot_001
```

Render a local-only review gallery:

```bash
python3 scripts/animal_image_pipeline.py render-review --batch pilot_001
```

Open `.image-review/pilot_001/index.html`, use the buttons, export decisions, and save them as `.image-review/pilot_001/decisions.json`.

Apply approved decisions and download approved images:

```bash
python3 scripts/animal_image_pipeline.py apply-decisions --file .image-review/pilot_001/decisions.json
python3 scripts/animal_image_pipeline.py download-approved
python3 scripts/build_site.py
python3 scripts/validate_site.py
```

## Public Site Behavior

- Approved animal photos display on cards and table rows.
- Each approved photo links back to its source.
- Cards show the credit, license, and provider.
- Pending animals continue to use the habitat image placeholder and an `Image pending` badge.

## Batch Size

Use `--limit 25` for the pilot batch. After approval flow is comfortable, use `--limit 100` for production batches.
