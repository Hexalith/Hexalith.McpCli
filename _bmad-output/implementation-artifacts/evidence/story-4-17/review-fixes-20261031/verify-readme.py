"""Verify the revised README locally with accepted packages and synthetic tokens.

Usage: python3 -I verify-readme.py <repository> <accepted-packages> <output-json>
No Gateway request or live command is made. Scratch homes are removed afterward.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile

repo, packages, output = map(Path, sys.argv[1:4])
raw = (repo / "README.md").read_bytes()
section = raw.decode().split("### Quick start: Claude Code sets it up for you\n", 1)[1].split("### Install into an isolated directory\n", 1)[0]
blocks = re.findall(r"```(\w*)\n(.*?)```", section, re.S)
prompt = next(b for lang, b in blocks if lang == "text" and b.startswith("Set up the Hexalith MCP server"))
steps = {m.group(1): m.group(2) for m in re.finditer(r"^(\d)\. (.+)$", prompt, re.M)}
start = next(b for lang, b in blocks if lang == "sh" and "mkdir -m 700" in b)
token_block = next(b for lang, b in blocks if lang == "sh" and "read -rsp" in b)
renew = next(b for lang, b in blocks if lang == "sh" and b.startswith('"$HOME/hexalith-operator/tools/hexalith" config set'))
teardown = next(b for lang, b in blocks if lang == "sh" and "claude mcp remove" in b)
owner = next(b for lang, b in blocks if lang == "sh" and "handoff=/absolute/path/handoff" in b)
expected = {"Hexalith.McpCli.1.2.0.nupkg": "eea29a8f6fde17b1cc780aa3a484753231eba6914b6b8401309269e393ddb37e",
            "Hexalith.McpCli.Abstractions.1.2.0.nupkg": "ab2d64f27c592286cb3721ffb6774ece2b745b86301eb36f48b22b821a443db3"}
hashes = {name: hashlib.sha256((packages / name).read_bytes()).hexdigest() for name in expected}
assert hashes == expected, "accepted-package-hash-mismatch"
results, assertions = [], {}
root = Path(tempfile.mkdtemp(prefix="mcpcli-417-review-readme-"))
home, handoff = root / "home", root / "handoff space $MCPCLI_417_LITERAL $(touch shell-marker)"
home.mkdir()
env = {k: v for k, v in os.environ.items() if not k.startswith(("EVENTSTORE_", "DOTNET_ROOT", "MCPCLI_HOME", "NUGET_"))}
env["HOME"] = str(home)
env["MCPCLI_417_LITERAL"] = "MUST-NOT-EXPAND"
values = {"HANDOFF": str(handoff), "TENANT": "tenant space $MCPCLI_417_LITERAL $(touch shell-marker)",
          "ACTOR": "actor's space $MCPCLI_417_LITERAL $(touch shell-marker)", "GATEWAY-URL": "http://127.0.0.1:18170"}
tokens = ("SYNTHETIC-OFFLINE-INITIAL", "SYNTHETIC-OFFLINE-RENEWED")
project = home / "hexalith-operator/project"
profile = home / "hexalith-operator/home/.eventstore/mcpcli.json"


def sub(command):
    command = command.replace('"HANDOFF/NuGet.Config"', shlex.quote(str(handoff / "NuGet.Config")))
    for key, value in values.items():
        command = re.sub(rf"(?<![A-Za-z_-]){re.escape(key)}(?![A-Za-z_-])", lambda _: shlex.quote(value), command)
    return command


def clean(value):
    value = value.replace(str(root), "<scratch>")
    for token in tokens:
        value = value.replace(token, "<synthetic-token>")
    return value


def run(label, command, cwd=None, stdin=None):
    proc = subprocess.run(["bash", "-c", command], cwd=cwd or project, env=env, input=stdin, capture_output=True, text=True, timeout=90)
    results.append({"label": label, "command": clean(command), "exitCode": proc.returncode, "stdout": clean(proc.stdout), "stderr": clean(proc.stderr)})
    return proc


try:
    cmd = owner.replace("handoff=/absolute/path/handoff", "handoff=" + shlex.quote(str(handoff))).replace("/absolute/path/accepted-packages", str(packages))
    r = run("owner handoff", cmd, root)
    assertions["ownerHandoffCreated"] = r.returncode == 0 and (handoff / "NuGet.Config").is_file()
    original_config = (handoff / "NuGet.Config").read_bytes()
    marker = handoff / "retained.nupkg"
    marker.write_text("retained")
    r = run("owner handoff refuses existing folder", cmd, root)
    assertions["ownerExistingFolderUnchanged"] = r.returncode != 0 and marker.read_text() == "retained" and (handoff / "NuGet.Config").read_bytes() == original_config
    marker.unlink()
    operator_root = home / "hexalith-operator"
    operator_root.mkdir()
    marker = operator_root / "retained-marker"
    marker.write_text("retain this existing directory")
    r = run("start refuses existing root", start.replace(" && claude", ""), home)
    assertions["existingQuickStartRootAndMarkerPreserved"] = r.returncode != 0 and operator_root.is_dir() and marker.read_text() == "retain this existing directory" and not project.exists()
    shutil.rmtree(operator_root)
    r = run("start folder without launching interactive client", start.replace(" && claude", ""), home)
    assertions["freshProjectCreated"] = r.returncode == 0 and project.is_dir()
    assertions["freshQuickStartRootMode700"] = stat.S_IMODE(operator_root.stat().st_mode) == 0o700
    r = run("install and version", sub(steps["1"]))
    assertions["acceptedToolVersion120"] = r.returncode == 0 and r.stdout.strip().splitlines()[-1:] == ["1.2.0"]
    status_check = '\nmcpcli_failure_status=$?\n[ "${token+x}" != x ] || exit 99\nexit "$mcpcli_failure_status"\n'
    r = run("token read failure preserves status and clears variable", sub(token_block) + status_check, stdin="")
    assertions["tokenReadFailurePreservedAndVariableCleared"] = r.returncode == 1 and not r.stdout and not r.stderr and not profile.exists()
    r = run("profile add failure preserves CLI status and clears variable", sub(token_block).replace(values["GATEWAY-URL"], "invalid-url") + status_check, stdin=tokens[0] + "\n")
    assertions["profileAddFailurePreservedAndVariableCleared"] = r.returncode == 2 and json.loads(r.stdout)["error"]["code"] == "configuration_invalid" and not r.stderr and not profile.exists() and tokens[0] not in r.stdout
    r = run("masked token command", sub(token_block), stdin=tokens[0] + "\n")
    assertions["initialTokenNotEchoed"] = r.returncode == 0 and tokens[0] not in r.stdout + r.stderr
    r = run("tenant actor and masked current", sub(steps["3"]))
    remaining = r.stdout
    while remaining.strip():
        shown, end = json.JSONDecoder().raw_decode(remaining.lstrip())
        remaining = remaining.lstrip()[end:]
    assertions["profileValuesAndMaskedToken"] = r.returncode == 0 and shown["tenant"] == values["TENANT"] and shown["actor"] == values["ACTOR"] and shown["url"] == values["GATEWAY-URL"] + "/" and "***" in shown["token"] and tokens[0] not in r.stdout + r.stderr
    current = json.loads(profile.read_text())["profiles"]["operator"]
    assertions["literalAnswersPreservedWithoutShellExpansion"] = current["tenant"] == values["TENANT"] and current["actor"] == values["ACTOR"] and not list(root.rglob("shell-marker"))
    r = run("register and connect", sub(steps["4"]))
    assertions["registeredStdioServerConnected"] = r.returncode == 0 and "Connected" in r.stdout
    r = run("renew token with documented command", sub(token_block), stdin=tokens[1] + "\n")
    document = json.loads(profile.read_text())
    current = document["profiles"]["operator"]
    assertions["renewalReplacesTokenAndClearsTenantActor"] = r.returncode == 0 and current["token"] == tokens[1] and current.get("tenant") is None and current.get("actor") is None
    prefix = 'export DOTNET_ROOT="$(dirname "$(readlink -f "$(command -v dotnet)")")" MCPCLI_HOME="$HOME/hexalith-operator/home"\n'
    r = run("restore tenant and actor after renewal", prefix + sub(renew))
    current = json.loads(profile.read_text())["profiles"]["operator"]
    assertions["renewalRestoresTenantAndActor"] = r.returncode == 0 and current["tenant"] == values["TENANT"] and current["actor"] == values["ACTOR"] and current["token"] == tokens[1]
    assertions["renewalRequiresClientRestart"] = "Restart Claude Code in `~/hexalith-operator/project` afterward" in section
    r = run("teardown registered server", teardown)
    assertions["registeredTeardownRemovesPrivateFolder"] = r.returncode == 0 and not (home / "hexalith-operator").exists()
    project.mkdir(parents=True)
    r = run("teardown without registration", teardown)
    assertions["absentRegistrationStillRemovesPrivateFolder"] = r.returncode == 0 and "No MCP server named" in r.stderr + r.stdout and not (home / "hexalith-operator").exists()
finally:
    shutil.rmtree(root)
    report = {"schema": "mcpcli-operator-review-fixes-verification/v1", "capturedAt": datetime.now(timezone.utc).isoformat(),
              "readmeSha256": hashlib.sha256(raw).hexdigest(), "packageHashes": hashes, "gatewayCalls": 0,
              "credentials": "synthetic only; no real token read", "assertions": assertions,
              "allAssertionsPass": len(assertions) == 17 and all(assertions.values()), "results": results,
              "limitations": ["No live Gateway, domain write or new operator timing.", "No fresh Claude Desktop/VS Code GUI session.", "Connection check covers stdio initialization only."]}
    output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"readmeSha256": report["readmeSha256"], "assertions": assertions, "allAssertionsPass": report["allAssertionsPass"]}, indent=2))
raise SystemExit(0 if report["allAssertionsPass"] else 1)
