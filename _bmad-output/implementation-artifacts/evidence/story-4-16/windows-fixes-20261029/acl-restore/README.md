# Explicit saved-ACL restoration

The parent inspected .NET 10.0.14 primary source while the Windows repair's CI
was running. FileInfo.SetAccessControl delegates to FileSecurity.Persist, which
writes only security sections marked modified; an unchanged GetAccessControl
snapshot has no modified sections. The denied-access fixture now imports the
saved access descriptor into a fresh FileSecurity, marking only Access modified,
before restoring it. Both normal verification and finally cleanup use the helper.
Owner, group and audit sections are not rewritten.

The required Windows fixture still verifies denied read/write access, the full
preflight error, empty stderr, unchanged profile bytes and restored target bytes.
Its read-after-restore assertion protects this correction. No skip, gate or
production check changed. Actual Windows execution remains pending.

The first local build rejected the unannotated helper with CA1416; the helper
now carries SupportedOSPlatform("windows"). The retained final Release build
passes with zero warnings/errors. No broader test rerun was needed for this
Windows-only test cleanup helper; the hosted CLI suite must exercise it.
