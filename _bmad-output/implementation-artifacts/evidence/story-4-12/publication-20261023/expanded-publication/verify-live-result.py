"""Verify a retained real run, including Gateway configuration isolation."""
import json
from pathlib import Path
import sys

run = Path(sys.argv[1])
result = json.loads((run / "result.json").read_text())
logs = json.loads((run / "log-provenance.json").read_text())
output = (run / "sanitized-runtime-extract.txt").read_text()
assert result["commandExitCode"] == 0, "The actual smoke command failed"
assert result["daprBeforeCommand"]["applications"] == [], "The private runtime was not empty"
assert result["commandElapsedSeconds"] < 900, "The outer smoke budget was exceeded"
assert set(result["ownedInfrastructureStopped"]) == {"sentry", "redis", "placement", "scheduler"}
assert all(code == 0 for code in result["ownedInfrastructureStopped"].values()), "Owned infrastructure did not exit successfully"
assert "Total: 1, Errors: 0, Failed: 0, Skipped: 0" in output, "Require one executed passing smoke"
assert logs["sampleMetadataMentions"] == 0, "Gateway inherited source-host sample registrations"
assert "/api/v1/queries - 200" in output, "The real Gateway request was not successful"
print("PASS: actual smoke, private cleanup, and test-owned Gateway configuration")
