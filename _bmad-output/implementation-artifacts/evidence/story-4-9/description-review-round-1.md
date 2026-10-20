# Catalog-only description review, round 1

Reviewer: fresh-context agent `story49_description_review`, given only
`catalog.json` and no Parties source or story context.

Artifact reviewed: `sha512-vTRzCDhnpvMWINNY3xGHi14EOPitkuj5k9Soh9+VvVNcSkl8V0IImFvNVHyxemCptEfBqqYAq8BGXQzHQ+prHA==`.

Verdict: **FAIL** for complete Catalog-only use. Basic creation and lifecycle
payloads were clear, but advertised changes required unstated rules.

| Severity | Catalog member | Finding |
| --- | --- | --- |
| Medium | `parties.update-party` description | Promises changing business identifiers, although the schema exposes only addition and removal. |
| Medium | Create/update `PersonDetails` and `OrganizationDetails` | Does not explain type compatibility, supplying both blocks, or whether an update changes party type. |
| Medium | `UpdateContactChannels[].Value` and list description | Does not explain omitted/null value behavior or the requirement for a non-null change. |
| Low | Contact `Value` descriptions | Postal-address and social-media representation is unclear. |
| Low | Contact `IsPreferred` descriptions | Preference scope and the effect on other preferred channels are unclear. |
| Low | `OrganizationDetails.IsNaturalPerson` | Restates the name without explaining business meaning or default. |
| Low | Lifecycle operation descriptions | Does not name the lifecycle and processing states that block the operation. |

Implementation follow-up: verify actual domain behavior before changing wording;
fix accurate findings without adding new domain rules, then repack and review the
updated Catalog in fresh context. Also expose the approved input bounds in the
composite descriptions. The original package is superseded when repacked; this
report remains bound to its original hash.
