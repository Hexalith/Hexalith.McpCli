---
title: 'Qualify FreeBSD x64 result target inspection'
type: 'chore'
created: '2026-12-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the Story 2.11 FreeBSD x64 ABI verification item. Run the existing CLI output test against fresh, existing, and symbolic-link targets on a native FreeBSD amd64 runtime.

</frozen-after-approval>

## Implementation Notes

Ran the Release CLI test assembly in a FreeBSD 14.4-RELEASE amd64 VM with native freebsd-x64 CoreCLR 11.0.0-rc.2.26504.105 and globalization invariant mode. The disposable guest used checksum-verified FreeBSD libunwind and libinotify packages.

`dotnet --fx-version 11.0.0-rc.2.26504.105 Hexalith.McpCli.Cli.Tests.dll -method Hexalith.McpCli.Cli.Tests.CliOutputContractTests.MutationPreflightRemovesProbeFilesAsync -failSkips` ran one test with zero failures and zero skips. It verifies output for a new file, replacement of an existing file and writing through a symbolic-link target while preserving the link. This qualifies the native output path with that runtime. Stable FreeBSD .NET 11 packaging remains unqualified.

- CLI inspection source SHA-256 `7a7fb86eda47631c2dd766c1257c9696078d6f7fcc25b34564df1da5afb3e143`
- Release test assembly SHA-256 `e39410d49978a5b1f07aeb7045a4b3eb1355337b925c6dc50d219fee1617e31e`
- Verification log SHA-256 `74949a78d183ecb3e8336436a0a80f3e29f0a2096e916ac26b5045125c649a83`
- FreeBSD 14.4 image SHA-256 `d957fe56fb596280428328e78e9e4feae00dd361701caa79a061f9bd289eff67`
- FreeBSD x64 runtime source archive SHA-256 `260b65b15495fee7c0013949b655d1bd0add128778c323163ac1fdeea6f6fcb2`
