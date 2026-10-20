# Catalog-only description review, round 2

Reviewer: fresh-context agent `story49_description_review_final`, given only
`catalog.json` and no Parties source or story context.

Artifact reviewed: `sha512-cRNu1OfMO46WwXg5IGMURPhux+sMb/iPsaBajLHv7kNXcd+6SkubQR+uJ+5EJm2TZHH4GPgixRfmgoHzDktDhQ==`.

Verdict: **PASS WITH NOTES**. The four operations are distinguishable, both
examples are usable, and the schemas explain ordinary creates, replacements
and child edits. Nested guidance on complete replacement, nullable updates,
raw contact values, case sensitivity and preference handling is useful.

| Severity | Catalog member | Remaining note |
| --- | --- | --- |
| Medium | Both composite descriptions | Distinguish the 128-character record/routing IDs from business identifier `Value` strings governed by the 512-character bound. |
| Medium | Update addition/removal lists | Explain removal overlap rejection and the existing behavior when a contact ID appears in both addition and update lists. |
| Low | Composite sub-operation cap | Explain creation/list/detail counting so callers can calculate the cap. |
| Low | Collection item schemas | Although generated schemas admit null items, upstream validators reject them; state that in the descriptions. |

All four notes are direct wording corrections to existing behavior. The final
description delta is to be recorded in `description-review-fixes.md`, with a
fresh artifact hash and Catalog. Domain behavior and original vectors remain
unchanged. The reviewed package is retained locally under `artifacts/round-2/`.
