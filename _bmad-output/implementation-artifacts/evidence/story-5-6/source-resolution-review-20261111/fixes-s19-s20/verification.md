# Review fixes S19/S20

Matrix project expressions now expand bounded independent job blocks into normal
literal arguments. The shell target reader has no encoded-token decoder.
Temporary parsing markers are chosen outside the original source text and are
removed before target inspection. Quoted multi-value matrices retain separate
full paths and job/step context. Forged source tokens cannot inherit an approved
project identity.

Nearest default metadata still supplies each project's properties. Every
unconsumed props/targets file, including standalone and shadowed defaults, is
parsed and classified independently. The S10 fixture now distinguishes those
source observations from falsely attributing the same metadata to its shadowed
library project.

The guide documents required/optional/SDK/nested imports, nearest metadata,
property limits, tool consumption versus definitions, literal matrix alternatives
and unsupported shell forms. Six targeted regression methods and ten directly
covering mutation controls pass; `git diff --check` passes. No full verification
or current-reference acceptance scan ran here.

The combined [runner](../mutation-guards.py) retains the previous 96 controls
with adapted matrix anchors and adds five S19/S20 controls (101 total).
`--round-two-only` runs the ten targeted controls; the default runs all controls.
The previous runner's exact bytes are preserved in
[mutation-guards-prior.py](mutation-guards-prior.py). [The verification receipt](verification.json)
binds the new sources and archive, while [the prior evidence manifest](prior-review-evidence.json)
records unchanged earlier artifacts. All original source-resolution packet bytes
and all other earlier review evidence remain unchanged.
