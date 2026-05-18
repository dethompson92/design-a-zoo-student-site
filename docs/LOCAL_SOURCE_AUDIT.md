# Local Source Asset Audit

Generated: 2026-05-18 01:33:48

## Verdict

- Do not publish any images from `untitled folder` directly into animal cards yet.
- Many local exports are technically reviewable, but they do not carry the source URL, author, license name, or license URL required by the animal image pipeline.
- Visual spot-checking shows the strongest `untitled folder` images are mostly worksheet pages, packet covers, trackers, rubrics, and planning sheets, not individual animal photos.
- The folder is still useful: it contains image-generation exports and conversation context that can guide future classroom-resource visuals after provenance is confirmed.
- The 100+ geometry worksheet images are useful for a separate classwork/worksheet resource page, not for the public animal-photo fields.
- `Zoo/Zoo_Design_Studio_Project/Student_Packet/` has cleaner student packet page images that are better candidates for a future resources page than the repeated exports.
- Teacher-key and answer materials should remain local-only.

## Counts

- Workspace images scanned outside the public site repo: 731
- Images inside `untitled folder`: 404
- Technically reviewable `untitled folder` images needing manual provenance review: 130
- Exact duplicate image groups: 178
- Near-duplicate perceptual groups: 279

## Technical Status

- needs work: 428
- reviewable: 303

## Source Categories

- archived packet page: 72
- habitat asset: 50
- local export image: 404
- student packet page: 52
- teacher guide page: 28
- worksheet image: 125

## Use Recommendations

- already-used habitat image: 50
- do not publish: 28
- hold for manual review: 404
- reference only: 249

## Useful Project Files Found

- `Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package/zoo_animals_student_database_final.csv`: already the correct public source of truth.
- `Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package/Design_a_Zoo_Digital_Animal_Database.html`: useful historical/reference copy, but the rebuilt static site should stay canonical.
- `Design_a_Zoo_GoogleDocs_Classwork_Teacher_Key_Bundle/Design_a_Zoo_GoogleDocs_Student_Classwork_Workbook.pdf`: useful student-facing classwork reference if a future resources page is added.
- `Design_a_Zoo_GoogleDocs_Classwork_Teacher_Key_Bundle/Design_a_Zoo_GoogleDocs_Answer_Key_and_Sample_Zoo.pdf`: teacher-only; do not publish.
- `Design_a_Zoo_Image_Generator_Master_Prompts_Bundle/Design_a_Zoo_Image_Generator_Master_Prompts_STUDENT.md`: useful for a future student image-generation guide.
- `Design_a_Zoo_Image_Generator_Master_Prompts_Bundle/Design_a_Zoo_Image_Generator_Master_Prompts_TEACHER.md`: teacher-only planning reference.
- `Zoo/Zoo_Geometry_Worksheets_100_Images_Final_20260514_031256/`: useful as a separate worksheet/geometry resource set after student/teacher separation.
- `Wild_Ecosystem_Habitats_Collection/`: already used for the 50 habitat images in the public site.

## Local Audit Artifacts

- `.image-review/local-source-audit/local_image_inventory.csv`: full image quality inventory.
- `.image-review/local-source-audit/local_image_summary.json`: machine-readable counts and duplicate groups.
- `.image-review/local-source-audit/local_image_candidates.json`: technically reviewable local exports that still require provenance/manual approval.
- `.image-review/local-source-audit/contact_sheet_untitled_candidates.jpg`: visual sample sheet for reviewable local exports.
- `.image-review/local-source-audit/contact_sheet_zoo_design_studio_export.jpg`: visual sample sheet for the larger Zoo Design Studio export.

## Required Checks Before Using Any Local Image

- Confirm ownership/provenance for the exact image file.
- Record source, credit, license/usage permission, and reviewer decision in a manifest before publishing.
- Reject worksheet screenshots, teacher-key pages, watermarked/stock-preview images, unclear rights, and images with text overlays that would confuse animal cards.
- Optimize approved images to `.webp` and keep them under `assets/animals/` only after approval.

## Notable File Records

- `Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package/Design_a_Zoo_Digital_Animal_Database.html`: reference only - Useful source context; publish only student-facing, non-answer materials.
- `Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package/zoo_animals_student_database_final.csv`: reference only - Useful source context; publish only student-facing, non-answer materials.
- `Design_a_Zoo_GoogleDocs_Classwork_Teacher_Key_Bundle/Design_a_Zoo_GoogleDocs_Answer_Key_and_Sample_Zoo.pdf`: reference only - Useful for classwork context; teacher-key material should stay out of the public repo.
- `Design_a_Zoo_GoogleDocs_Classwork_Teacher_Key_Bundle/Design_a_Zoo_GoogleDocs_Student_Classwork_Workbook.pdf`: reference only - Useful for classwork context; teacher-key material should stay out of the public repo.
- `Design_a_Zoo_Image_Generator_Master_Prompts_Bundle/Design_a_Zoo_Image_Generator_Master_Prompts_STUDENT.md`: reference only - Useful for future image-generation prompts, not a publishable animal image source.
- `Design_a_Zoo_Image_Generator_Master_Prompts_Bundle/Design_a_Zoo_Image_Generator_Master_Prompts_TEACHER.md`: reference only - Useful for future image-generation prompts, not a publishable animal image source.
