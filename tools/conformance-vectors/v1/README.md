# Conformance vector contract v1

This directory is the McpCli-owned, test-only contract for Module conformance vectors. `schema.json` is closed at every contract-owned object; `payload`, `expectedGateway.body`, and `scriptedResponse.body` remain JSON data supplied by the owning Module. Only `formatVersion: 1` is supported. An incompatible format needs a new versioned directory and an explicit validator update. Production code never loads these files.

Each vector names one canonical decorated Operation and its owning Contracts **package ID and exact version**. The owning Module repository stores and approves its real vectors. The three `sample-*.json` vectors cover the local synthetic Contracts fixture; they do not enroll a production Module.

## Authoring and approval

Create a vector using `schema.json` and the synthetic examples. `prerequisites` are generic calls run before the invocation; `postconditions` are generic calls run after it. Every call fixes an Operation, kind, Payload, Envelope, Gateway request expectation, scripted response, and result assertions. Use postcondition Queries to assert the observable effect of a Command without submitting that live Command twice.

`expectedGateway.body` lists fields that the runner must compare against the captured request, including routing, Envelope, submitted Payload, and paging. It is a required-field projection; the runner separately compares complete captured requests from both Heads. The submitted Payload can differ from the input Payload where Core fills or removes envelope-owned properties. `maskGenerated` may name only a generated Command `/messageId` or `/correlationId`, with `<generated>` at that location in the expected body. Caller-supplied identifiers, especially an idempotency key, remain exact. `echoRequestFields` tells the loopback script to copy the selected request identifiers into its response.

Assertion paths are RFC 6901 JSON Pointers into the canonical result document. The operators are `equals` (JSON structural equality), `exists` (boolean), `arrayLength` (nonnegative integer), and `contains` (array member, object field subset, or string fragment). Every call needs at least one assertion. A Command can assert `/status` and a postcondition Query can assert actual `/document` content. Paging cases should request a non-default page size and subsequent cursor and assert contents, not just a successful status.

Install the **test tooling** dependency with `python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt`. From the repository root, validate against the owning immutable Contracts release artifact before Module maintainer approval:

```sh
python3 tools/conformance-vectors/v1/validate.py \
  --artifact /path/to/Owner.Contracts.1.2.3.nupkg \
  /path/to/module/vectors/*.json
```

The shared entry point `validate_vectors(paths, artifact, expected_package, expected_operations)` applies the same checks in a runner. Before either runner lane, pass the restored flagged production package ID and exact version with `--expected-package-id` and `--expected-package-version`. A JSON array of canonical Catalog names can be passed with `--operations-file` to reject missing, extra, or duplicate vectors. The loopback runner reads the test host's generated flagged manifest and rejects missing, extra, duplicate, or wrong-kind vectors for the owning package. It also compares the immutable artifact's SHA-512 with the package restored into that host. The validator itself has no production Catalog dependency.

For the complete local sample gate, run `bash tools/conformance-vectors/v1/run-sample-loopback.sh`. It packs the sample and Abstractions into a temporary feed, restores the test-only host into an isolated NuGet cache, builds it, runs the validator tests, and executes all three vectors through separate CLI and MCP stdio processes. The generated manifest contains only the flagged sample package; production source and its package manifest stay unchanged. The test host invokes the actual CLI/MCP composition through a reflection adapter because the sample package is intentionally absent from the production tool.

The equivalent validator-only check against an already packed sample artifact is:

```sh
dotnet pack tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj --configuration Release -p:IsPackable=true -p:Version=1.0.0 --output /tmp/mcpcli-conformance-pack
python3 tools/conformance-vectors/v1/validate.py \
  --artifact /tmp/mcpcli-conformance-pack/Hexalith.McpCli.Sample.Contracts.1.0.0.nupkg \
  --expected-package-id Hexalith.McpCli.Sample.Contracts \
  --expected-package-version 1.0.0 \
  tools/conformance-vectors/v1/sample-command.json \
  tools/conformance-vectors/v1/sample-query.json \
  tools/conformance-vectors/v1/sample-rename.json
python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'
```

`run_loopback.py` drives both Heads out of process. For every vector it compares discovery documents, invokes each prerequisite, invocation, and postcondition against separately reset HTTP response scripts, checks semantic result assertions, compares complete captured Gateway requests and their required fields, and checks malformed-Payload error parity without a Gateway request. Only generated Command message and correlation ULIDs are masked; caller-supplied values remain exact. Run it once per owning package, supplying all of that package's vectors and the host containing its flagged Contracts release.

The once-per-vector live Aspire semantic lane remains a separate AD-16 gate. The synthetic sample's scripted Query response illustrates assertions; it does not prove a real handler's persistent effect.
