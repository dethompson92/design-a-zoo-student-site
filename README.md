# Design a Zoo Student Website

Public student-facing animal and habitat database for the Design a Zoo project.

## What Is Published

- A searchable animal-choice website for students.
- 1,844 animal entries from the clean student database.
- 50 habitat records with copied habitat images.
- Phase 2 fields for approved animal images, credits, source URLs, providers, and licenses.
- A validation script and audit report.

## What Is Not Published

- Teacher guides, answer materials, raw Genspark exports, archive folders, and working packet files.
- The larger contaminated generated CSVs.
- The polluted generated `animals/` markdown folder.

## Local Preview

Run from this folder:

```bash
python3 -m http.server 4173
```

Then open:

```text
http://localhost:4173/
```

## Rebuild Data

Run from this folder after updating the source CSV or habitat images in the parent project:

```bash
python3 scripts/build_site.py
python3 scripts/validate_site.py
```

## Animal Image Pipeline

The site supports one approved image per unique animal name. Candidate discovery and approval are intentionally separate and local-only so unlicensed images do not get published by accident.

```bash
python3 scripts/animal_image_pipeline.py init-manifest
python3 scripts/animal_image_pipeline.py find-candidates --limit 25 --batch pilot_001
python3 scripts/animal_image_pipeline.py render-review --batch pilot_001
```

Open `.image-review/pilot_001/index.html`, approve/reject candidates, export the decisions JSON, then apply and download only approved images:

```bash
python3 scripts/animal_image_pipeline.py apply-decisions --file .image-review/pilot_001/decisions.json
python3 scripts/animal_image_pipeline.py download-approved
python3 scripts/build_site.py
python3 scripts/validate_site.py
```

See `docs/IMAGE_PIPELINE.md` for the full workflow and safety rules.

## Classroom Data Note

Values are simplified for math modeling and student design decisions. They are not real animal-care standards.
