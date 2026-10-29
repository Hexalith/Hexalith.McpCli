# CLI diagnostic-order correction

CI [40879087695](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40879087695) rejected source `630ea7f29c02f6d10b19eae1136e01538527266e` because the existing `QueryPreflightRunsAfterNoResultChecksAsync` test assumed its one format note was the last stderr line. The retained job log shows the complete note followed by the buffered HTTP `End processing` message. The documented contract requires exactly one format note on stderr and does not order diagnostic messages relative to it. This failed run grants no staging acceptance.

The direct test correction requires one complete note line anywhere, keeps the duplicate-note check, and removes only that exact line before checking the complete catalog/HTTP diagnostics. Stdout, file contents, request count and all preflight assertions remain intact. Production code and documentation contracts are unchanged.

The focused CLI Release build passed without warnings or errors. Both worker and parent ran the entire output-contract class: 22 passed, two Windows-only skips and zero failures. Exact commands, parent XML and original CI failure are retained. The exact commit message passed pinned commitlint before use. Fresh exact-source CI remains required before staging.
