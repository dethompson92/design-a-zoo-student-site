# Design a Zoo Student Website

Public student-facing animal and habitat database for the Design a Zoo project.

## What Is Published

- A searchable animal-choice website for students.
- 1,844 animal entries from the clean student database.
- 50 habitat records with copied habitat images.
- Phase 2 fields for future animal images: `animal_image_path`, `image_alt`, `image_credit`, and `image_source`.
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

## Classroom Data Note

Values are simplified for math modeling and student design decisions. They are not real animal-care standards.
