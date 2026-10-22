# Read-only CodeQL build-mode contingency

No mode, source, filter, query or workflow change is applied or authorized by
this assessment. Run **39693568159** on **c8a0e9af8014a588f9ac9b855b7f2f093fd51a86**
remains binding with its existing 120-minute limit.

C# `none` mode combines repository source and inferred dependencies; GitHub
documents limitations when dependency versions or class names collide. Traced
builds can capture the actual compilation and generated code, but that changes
which files enter analysis. This is a coverage decision, not an equivalent
one-line configuration substitution. [GitHub C# build documentation](https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages).

The [complete source inventory](eventstore-codeql-build-mode-contingency.json)
retains every one of the **60** real project files, all 33 explicit Compile
overrides and 21 conditional/dynamic references. The solution names 51 projects;
static literal references reach 54. PayloadProtection, its tests and four P1R
consumer projects remain outside that closure. Static inspection is not proof
of an evaluated Release graph. The current 15,180 C# inputs also include 11,408
captured files, 55 documentation files, and conditional or uncompiled fixtures.
Every source difference would need explanation.

The present shared job checks out without submodules, initializes CodeQL, then
analyzes. Manual mode would need a genuine traced build between those steps;
GitHub defines its coverage by the source that build compiles.
[Manual-build documentation](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/manage-your-configuration/codeql-for-compiled-languages).

Any later proposal would need to:

- Initialize the exact root Builds gitlink, provision SDK 10.0.402, and preserve
  Release plus `UseHexalithProjectReferences=false`.
- Cold-build all intended production, tests and consumer graphs under CodeQL,
  including the separate project families and their owning conditions.
- Retain actual compiler inputs and generated-source extraction, compare them
  with every current category, and explain all omissions and additions.
- Preserve the security queries/upload controls, obtain an explicit decision
  about coverage differences, and qualify the resulting source afresh.

CLI 2.27.3 supports language-specific solution discovery, including `.slnx`;
its inspected `dotnet build` command does not itself select Release. Actual
autobuild behavior here has not been tested.
[Discovery source](https://github.com/github/codeql/blob/a1575b98a8cc19bcfa7bb6cb41be688cb3dae65c/csharp/autobuilder/Semmle.Autobuild.Shared/Autobuilder.cs#L172),
[C# solution extension](https://github.com/github/codeql/blob/a1575b98a8cc19bcfa7bb6cb41be688cb3dae65c/csharp/extractor/Semmle.Util/Language.cs#L6),
[build-command source](https://github.com/github/codeql/blob/a1575b98a8cc19bcfa7bb6cb41be688cb3dae65c/csharp/autobuilder/Semmle.Autobuild.CSharp/DotNetRule.cs#L133).
