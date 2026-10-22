# Bounded local CodeQL comparison

Both official versions reached the local thirty-minute extraction limit. Neither completed extraction; no query phase or security qualification was run. Current PR CodeQL run 39693568159 remains binding.

| CLI | Trace seconds | Exit | Aggregate peak MiB | Observed process CPU seconds |
| --- | ---: | ---: | ---: | ---: |
| 2.27.2 | 1800.808 | 143 | 2964.082 | 6830.41 |
| 2.27.3 | 1801.025 | 143 | 2955.223 | 6849.50 |

Each run rechecked all 16,248 frozen input hashes successfully and left its task-owned process group empty. Both retained 15,180 C# sources, 566 projects, 592 resolved references, zero unresolved references, 1,665 assembly conflicts and 75 generated sources before extraction. Working-file counts/bytes stayed static after extraction began; no TRAP files appeared before either cutoff.

The late 2.27.3 snapshot places the main thread in compiler diagnostics and two workers in method binding/compilation, including invocation/await and task-type normalization. Snapshots locate work; they do not establish a hot loop or eventual completion.

Both versions used the same unconstrained local host affinity/cgroup and four-thread/14,570-MiB CLI hints. Managed work exceeded four cores during parts of each run. Versions ran sequentially with ordinary shared caches; only the second has brief recorded stack captures. These are not GitHub-equivalent physical/cgroup limits, so no absolute CI timing or version-regression inference is made.

The [compact comparison](eventstore-codeql-local-version-comparison.json) binds the exact private original, commands, logs, two-second samples, inputs and cleanup. [Minute resource curves](eventstore-codeql-local-resource-curves.jsonl), [output progress](eventstore-codeql-local-output-progress.json), and both managed-stack reports retain the safe measurements. The complete 143,956-byte original is private with SHA256 `fd1b6b2e5551106e93909308ab8a4cd9f8b5664ea5e3abac8753ef4ff989d6a1`. The 15,070,927-byte source-preparation original is also private, bound by the [compact snapshot metadata](eventstore-codeql-local-source-snapshots.json).

Production and full-v1 acceptance remain false.

The 16,248-file equality manifest selects tracked `.cs`, `.csproj`, `.props`, `.targets`, `.slnx` paths plus root `.gitattributes`, `.gitmodules`, `global.json` and `nuget.config`. The other 29,088 tracked entries were outside that before/after hash check. The complete initial Git tree remains bound separately; no all-tracked-byte preservation claim is made for the two original runs.
