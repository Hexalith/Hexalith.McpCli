# Conformance vector contract v1

This directory is the McpCli-owned, test-only contract for Module conformance vectors. Only `formatVersion: 1` is supported. `schema.json` defines structural rules; `validate.py` applies them with strict integer typing and adds cross-field consistency and artifact identity checks. Authors and runners must use this shared validator for the complete approval rules; schema validation alone is insufficient. Production code never loads these files. An incompatible format needs a new versioned directory and an explicit validator update. Tightening validation of malformed v1 inputs does not introduce a new format.

Each vector names one canonical decorated Operation and its owning Contracts **package ID and exact version**. Package IDs compare case-insensitively; versions compare exactly, without case folding or version normalization. A vector approved for one version is stale when its package version changes, even if its Operation Name is reused. The owning Module repository stores and approves its real vectors. The three `sample-*.json` vectors cover the local synthetic Contracts fixture; they do not enroll a production Module.

## Contract rules

Create a vector using `schema.json` and the synthetic examples. `prerequisites` are generic calls run before the invocation; `postconditions` are generic calls run after it. Every call fixes an Operation, kind, Payload, Envelope, Gateway request expectation, scripted response, and result assertions. Command Payload roots are objects. Query Payload roots may be any finite JSON value: object, array, string, number, boolean, or null. The invocation's Operation and kind must match the vector header. Canonical names contain exactly two dot-separated lowercase ASCII alphanumeric kebab-case parts, including digit-leading parts such as `1-module.2-operation`.

The root, package, call, Envelope, Gateway expectation, scripted response, assertion, and Gateway request-body objects reject unknown fields. Call `payload`, the nested Gateway `payload`, and `scriptedResponse.body` remain Module-owned JSON data, as do assertion values. Arbitrary fields and nested JSON are allowed there; duplicate JSON keys and nonfinite numbers (`NaN`, `Infinity`, or numeric overflow) are rejected. Tenants use the runtime Gateway grammar: 1–64 lowercase ASCII letters, digits, or hyphens, starting and ending with a letter or digit. Required routing strings and supplied actor, aggregate ID, entity ID, and cursor strings cannot be blank. Caller-supplied correlation and idempotency identifiers use the v1 ULID pattern. Envelope identifiers are independent of the Module's payload Identifier Kind.

Contract integer fields (`formatVersion`, `pageSize`, `offset`, `statusCode`, and `arrayLength` values) require integer JSON tokens: `1.0`, `1e0`, and booleans are invalid even when Python would compare them equal to integers. Query offsets range from 0 through 2147483647. Module-owned JSON numbers retain their normal finite numeric representation.

`expectedGateway.body` is the complete captured Gateway request body, including all emitted routing, Envelope, submitted Payload, and paging fields; unknown, missing, and mistyped Gateway-owned fields are rejected. The runner compares it completely with each Head's captured body. Every Command includes `messageId`, `correlationId`, and an object `payload`. Every Query includes `projectionType`; the synthetic Query pins it to `sample-items`. A non-null Query Payload is emitted, while a JSON null Query Payload is omitted from the wire body. The submitted Payload can differ from the input Payload where Core fills or removes envelope-owned properties. Supplied extensions and paging must match the expected request exactly, including paging value types. A supplied extensions map cannot be empty; omit it to supply none. Core omits empty maps from both heads' Gateway requests, and omission is the single canonical vector form. When those inputs are absent, their request fields must be absent too. Command-only and Query-only inputs and Gateway request fields cannot be mixed. A Query cannot combine cursor and offset.

`maskGenerated` may name only a generated Command `/messageId` or `/correlationId`, with `<generated>` at that location in the expected body. Caller-supplied identifiers, especially an idempotency key, remain exact. `echoRequestFields` tells the loopback script to copy selected request identifiers into its response: a Command response must echo correlation ID and may echo message ID. A Query has no request identifiers to mask or echo; its response may still contain a scripted correlation ID supplied by the Module.

Assertion paths are RFC 6901 JSON Pointers into the canonical result document; the empty pointer addresses the whole result. The operators are `equals` (JSON structural equality), `exists` (boolean value), `arrayLength` (nonnegative integer value), and `contains` (array member, object field subset, or string fragment). JSON equality is recursive and type-preserving: integers and floats are Numbers and compare by numeric value, while booleans never equal numbers. Every assertion requires a value and every call needs at least one assertion. A Command can assert `/status` and a postcondition Query can assert actual `/document` content. Paging cases should request a non-default page size and subsequent cursor and assert contents, not just a successful status.

## Offline sample gate

Install the test tooling dependency with `python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt` (use a virtual environment if required). The repository's pinned .NET SDK and root-declared Builds submodule must be available for packing. From the repository root:

```sh
# Local development defaults to Debug.
bash tools/conformance-vectors/v1/run-sample-validation.sh

# The independent conformance-vector-contract CI job uses Release.
bash tools/conformance-vectors/v1/run-sample-validation.sh Release
```

The script packs only the sample Contracts project and builds its dependencies, runs the offline validator and existing runner unit tests, then validates all three examples against the packed `Hexalith.McpCli.Sample.Contracts` version `1.0.0` artifact and expected identity. It prints the result and artifact SHA-512 as `sha512-` plus base64, matching the runner's NuGet restored-package hash format. It uses Python's standard library for hashing on Linux and macOS, exits 0 on success, and cleans only its own temporary artifact/build directory. It builds neither Head and needs no Gateway or AppHost. Packing may restore build dependencies from NuGet; “offline” means validation and unit tests need no network service or running application.

For the focused Python checks alone:

```sh
python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'
```

## Module author approval

1. Store the vector set in the owning Module repository and name the immutable owning Contracts `.nupkg` package ID and exact version in every vector. Use postcondition Queries to assert a Command's observable effect without submitting that live Command twice.
2. Obtain that immutable artifact and run the shared validator against it. No Head, Catalog assembly loading, Gateway, or AppHost is required for author approval:

   ```sh
   python3 tools/conformance-vectors/v1/validate.py \
     --artifact /path/to/Owner.Contracts.1.2.3.nupkg \
     --expected-package-id Owner.Contracts \
     --expected-package-version 1.2.3 \
     /path/to/module/vectors/*.json &&
   python3 - /path/to/Owner.Contracts.1.2.3.nupkg <<'PY'
   import base64
   import hashlib
   import sys
   from pathlib import Path

   artifact = Path(sys.argv[1])
   digest = base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode("ascii")
   print(f"sha512-{digest}  {artifact}")
   PY
   ```

3. Resolve every finding and rerun until exit 0. Invalid or incompatible vectors exit 1, with source, location, and reason diagnostics. CLI usage errors exit 2. Package identity comes from the artifact's root `.nuspec`, never a project file.
4. Record maintainer approval with `formatVersion: 1`, the vector repository revision, validator revision, owning package ID and exact version, immutable artifact location and NuGet-compatible `sha512-` base64 hash, exact validation command, successful output/exit code, and approving maintainer. Keep the artifact available for downstream checks; the temporary sample artifact is illustrative evidence only.

Approval establishes format, script consistency, and artifact identity compatibility. It does not establish that an Operation exists in the owning Catalog, that its kind or Payload matches the decorated Contracts schema, or that a handler produces the scripted semantic result. Those checks belong to the downstream gates below.

## Runner handoff

The reusable entry point `validate_vectors(paths, artifact, expected_package, expected_operations)` applies the same schema, consistency, and artifact checks as the CLI. A JSON array of canonical Catalog names can be passed with `--operations-file` to reject missing, extra, or duplicate vectors. The validator itself has no production Catalog dependency.

**Story 4.11** owns production restored-package rechecks and deterministic cross-head parity. Before execution, the runner supplies the restored flagged production package ID and exact version to the shared validator (`--expected-package-id` and `--expected-package-version` on the CLI), checks coverage and kinds against the owning Catalog, and checks Payload compatibility. It must also verify that the immutable artifact matches the package restored into the host. This catches a stale approval after a package update.

The existing sample parity gate remains available independently as `bash tools/conformance-vectors/v1/run-sample-loopback.sh`, and CI retains it in the separate `conformance-vector-loopback` job. It packs the sample and Abstractions into a temporary feed, restores the test-only host into an isolated NuGet cache, builds it, runs the validator tests, and executes all three vectors through separate CLI and MCP stdio processes. The generated manifest contains only the flagged sample package; production source and its package manifest stay unchanged. The test host invokes the actual CLI/MCP composition through a reflection adapter because the sample package is intentionally absent from the production tool. The runner compares the immutable artifact's SHA-512 with the package restored into that host.

`run_loopback.py` drives both Heads out of process. For every vector it compares discovery documents, invokes each prerequisite, invocation, and postcondition against separately reset HTTP response scripts, checks semantic result assertions, compares complete captured Gateway requests and their required fields, and checks malformed-Payload error parity without a Gateway request. Only generated Command message and correlation ULIDs are masked; caller-supplied values remain exact. Run it once per owning package, supplying all of that package's vectors and the host containing its flagged Contracts release. Passing offline author approval does not require running this parity gate.

**Story 4.13** owns the separate live EventStore/Aspire semantic lane. It rechecks the approved vectors against the restored owning package using the shared validator, runs each vector once, and verifies actual Query contents and persistent Command effects. The synthetic sample's scripted Query response illustrates assertions; it does not prove a real handler's persistent effect. Live Commands are not submitted twice solely for cross-head byte equality.
