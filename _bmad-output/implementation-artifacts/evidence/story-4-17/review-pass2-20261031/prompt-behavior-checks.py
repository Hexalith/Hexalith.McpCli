"""Check the README quick-start prompts with the real Claude Code CLI, without executing any command.

Usage: python3 -I prompt-behavior-checks.py <repository> <output-json>

Claude Code runs in an empty scratch project with no MCP servers (--strict-mcp-config) and a
settings file that forces every Bash call to "ask". In print mode an "ask" cannot be approved,
so each attempted command is refused and recorded in permission_denials instead of running.
The refused commands are then replayed in a sandbox where `dotnet` is a shell function and the
tool is a stub that only records its arguments, proving how the operator's answers were quoted.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

repo, output = Path(sys.argv[1]), Path(sys.argv[2])
raw = (repo / "README.md").read_bytes()
section = raw.decode().split("### Quick start: Claude Code sets it up for you\n", 1)[1].split("### Install into an isolated directory\n", 1)[0]
blocks = re.findall(r"```(\w*)\n(.*?)```", section, re.S)
setup_prompt = next(b for lang, b in blocks if lang == "text" and b.startswith("Set up the Hexalith MCP server"))
task_prompt = next(b for lang, b in blocks if lang == "text" and b.startswith("Use only the hexalith MCP tools"))

root = Path(tempfile.mkdtemp(prefix="mcpcli-417-prompt-check-"))
project, sandbox, home = root / "project", root / "sandbox", root / "home"
for folder in (project, sandbox, home):
    folder.mkdir()
values = {"HANDOFF": str(root / "handoff space $MCPCLI_417_LITERAL $(touch shell-marker)"),
          "TENANT": "tenant space $MCPCLI_417_LITERAL $(touch shell-marker)",
          "ACTOR": "actor's space $MCPCLI_417_LITERAL $(touch shell-marker)"}
Path(values["HANDOFF"]).mkdir()
(Path(values["HANDOFF"]) / "NuGet.Config").write_text("<configuration />\n")
settings = root / "ask-bash-settings.json"
settings.write_text(json.dumps({"permissions": {"ask": ["Bash"]}}))
flags = ["--output-format", "json", "--permission-mode", "default", "--settings", str(settings),
         "--strict-mcp-config", "--mcp-config", json.dumps({"mcpServers": {}})]
version = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=60).stdout.strip()


def clean(value):
    return value.replace(str(root), "<scratch>") if isinstance(value, str) else value


def claude(prompt, session=None, max_turns=6):
    argv = ["claude", "-p", prompt, *flags, "--max-turns", str(max_turns)] + (["--resume", session] if session else [])
    proc = subprocess.run(argv, cwd=project, capture_output=True, text=True, timeout=600)
    result = json.loads(proc.stdout)
    denials = [{"tool": d.get("tool_name"), "command": clean((d.get("tool_input") or {}).get("command"))} for d in result.get("permission_denials", [])]
    return result, {"exitCode": proc.returncode, "numTurns": result.get("num_turns"), "models": sorted((result.get("modelUsage") or {}).keys()),
                    "permissionDenials": denials, "reply": clean(result.get("result"))}


def replay(command, capture):
    """Replay a refused command with `dotnet` and the tool stubbed; return the recorded argument lists."""
    tools = home / "hexalith-operator/tools"
    tools.mkdir(parents=True, exist_ok=True)
    stub = tools / "hexalith"
    stub.write_text('#!/bin/bash\nprintf "%s\\0" "$@" >> "$CAPTURE"\nprintf "\\36\\0" >> "$CAPTURE"\n')
    stub.chmod(0o700)
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "CAPTURE": str(capture), "MCPCLI_417_LITERAL": "MUST-NOT-EXPAND"}
    prefix = 'dotnet(){ printf "%s\\0" dotnet "$@" >> "$CAPTURE"; printf "\\36\\0" >> "$CAPTURE"; return 1; }\n'
    proc = subprocess.run(["bash", "-c", prefix + command], cwd=sandbox, env=env, capture_output=True, text=True, timeout=60)
    calls, current = [], []
    for item in (capture.read_bytes().split(b"\0")[:-1] if capture.exists() else []):
        if item == b"\x1e":
            calls.append(current)
            current = []
        else:
            current.append(item.decode())
    return proc.returncode, calls


checks, assertions = {}, {}
try:
    first, record = claude(setup_prompt, max_turns=4)
    checks["setupTurn1"] = record
    assertions["setupAsksBeforeRunning"] = record["permissionDenials"] == [] and all(w in record["reply"].lower() for w in ("handoff", "tenant", "actor"))
    session = first["session_id"]
    answers = f"Handoff folder: {values['HANDOFF']}\nTenant: {values['TENANT']}\nActor: {values['ACTOR']}"
    _, record = claude(answers, session)
    checks["setupTurn2Answers"] = record
    step1 = next((d["command"] for d in record["permissionDenials"] if d["tool"] == "Bash" and "dotnet tool install" in (d["command"] or "")), None)
    assertions["step1AttemptedOnlyAfterAnswers"] = step1 is not None and "HANDOFF" not in step1
    if step1:
        code, calls = replay(step1.replace("<scratch>", str(root)), root / "step1.args")
        install = next((c for c in calls if c[:3] == ["dotnet", "tool", "install"]), [])
        checks["step1Replay"] = {"exitCode": code, "calls": [[clean(a) for a in c] for c in calls]}
        assertions["step1HandoffPathLiteral"] = "--configfile" in install and install[install.index("--configfile") + 1] == values["HANDOFF"] + "/NuGet.Config"
    _, record = claude("The Bash call was refused only because this check cannot approve commands. Treat step 1 as done: the last line was 1.2.0. Continue with step 2.", session)
    checks["setupTurn3"] = record
    _, record = claude("Done. I ran the token command in my other terminal.", session)
    checks["setupTurn4"] = record
    step3 = next((d["command"] for t in ("setupTurn3", "setupTurn4") for d in checks[t]["permissionDenials"] if d["tool"] == "Bash" and "config set operator tenant" in (d["command"] or "")), None)
    assertions["step3AttemptedWithoutPlaceholders"] = step3 is not None and not re.search(r"(?<![A-Za-z_-])(TENANT|ACTOR)(?![A-Za-z_-])", step3)
    if step3:
        code, calls = replay(step3.replace("<scratch>", str(root)), root / "step3.args")
        checks["step3Replay"] = {"exitCode": code, "calls": [[clean(a) for a in c] for c in calls]}
        assertions["step3TenantAndActorLiteral"] = ["config", "set", "operator", "tenant", values["TENANT"]] in calls and ["config", "set", "operator", "actor", values["ACTOR"]] in calls
    assertions["noShellExpansionMarker"] = not list(root.rglob("shell-marker"))
    _, record = claude(task_prompt, max_turns=4)
    checks["taskTurn1"] = record
    assertions["taskAsksBeforeAnyTool"] = record["permissionDenials"] == [] and "tenant" in record["reply"].lower() and "party" in record["reply"].lower()
finally:
    shutil.rmtree(root)
    report = {"schema": "mcpcli-operator-prompt-behavior-checks/v2", "capturedAt": datetime.now(timezone.utc).isoformat(),
              "readmeSha256": hashlib.sha256(raw).hexdigest(), "claudeCode": version,
              "method": "claude -p with --permission-mode default, a settings file forcing Bash to ask, --strict-mcp-config with no servers, in an empty scratch project; every Bash attempt is refused and recorded, then replayed with dotnet and the tool stubbed. Turn 3 tells Claude that step 1 is done because this harness cannot approve it; that is harness assistance, not operator procedure.",
              "values": {k: clean(v) for k, v in values.items()}, "assertions": assertions,
              "allAssertionsPass": len(assertions) == 7 and all(assertions.values()), "checks": checks,
              "limitations": ["No command actually ran; no install, profile, registration, Gateway call or timing.", "Model output varies between runs; this is one sample."]}
    output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"readmeSha256": report["readmeSha256"], "claudeCode": version, "assertions": assertions, "allAssertionsPass": report["allAssertionsPass"]}, indent=2))
raise SystemExit(0 if report["allAssertionsPass"] else 1)
