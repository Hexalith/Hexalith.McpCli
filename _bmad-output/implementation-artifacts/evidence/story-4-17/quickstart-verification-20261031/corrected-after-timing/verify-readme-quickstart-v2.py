"""Run the README quick-start commands verbatim (placeholders substituted) in fresh shells under a scratch HOME, with assertions.

Usage: verify-readme-quickstart-v2.py <readme> <scratch-root> <handoff-packages> <protected-profile> <output-json>
The token is piped from the protected profile into the README's masked read; it is never printed.
No Gateway call is made (the task environment has been removed).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

readme, root, packages, protected, output = sys.argv[1:6]
raw = open(readme, "rb").read()
text = raw.decode("utf-8")
section = text.split("### Quick start: Claude Code sets it up for you\n", 1)[1].split("### Install into an isolated directory\n", 1)[0]
blocks = re.findall(r"```(\w*)\n(.*?)```", section, re.S)
start_block = next(b for lang, b in blocks if lang == "sh" and "claude" in b and "mkdir -p" in b)
prompt = next(b for lang, b in blocks if lang == "text" and b.startswith("Set up the Hexalith MCP server"))
token_block = next(b for lang, b in blocks if lang == "sh" and "read -rsp" in b)
owner_block = next(b for lang, b in blocks if lang == "sh" and "handoff=/absolute/path/handoff" in b)
teardown_block = next(b for lang, b in blocks if lang == "sh" and "claude mcp remove hexalith" in b)
steps = {m.group(1): m.group(2) for m in re.finditer(r"^(\d)\. (.+)$", prompt, re.M)}

home, handoff = os.path.join(root, "home"), os.path.join(root, "handoff")
os.makedirs(home)
values = {"HANDOFF": handoff, "TENANT": "mcpcli-417-20261031-155f9b6d",
          "ACTOR": "mcpcli-417-operator-20261031-155f9b6d", "GATEWAY-URL": "http://127.0.0.1:18170"}
env = {k: v for k, v in os.environ.items() if not k.startswith(("EVENTSTORE_", "DOTNET_ROOT", "MCPCLI_HOME", "NUGET_"))}
env["HOME"] = home
token = json.load(open(protected))["profiles"]["operator"]["token"]


def sub(command):
    for key, value in values.items():
        command = re.sub(rf"(?<![A-Za-z_-]){re.escape(key)}(?![A-Za-z_-])", value, command)
    return command


def clean(s):
    return s.replace(root, "<root>").replace(token, "<token>")


def run(label, command, cwd, stdin=None):
    try:
        proc = subprocess.run(["bash", "-c", command], cwd=cwd, env=env, input=stdin, capture_output=True, text=True, timeout=240)
        code, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        code, out, err = "timeout", e.stdout or "", e.stderr or ""
    return {"label": label, "exit": code, "stdout": clean(out).strip().splitlines()[-12:], "stderrTail": clean(err).strip().splitlines()[-4:], "_full": clean(out)}


results, asserts = [], {}
project = os.path.join(home, "hexalith-operator", "project")
try:
    owner = owner_block.replace("/absolute/path/handoff", handoff).replace("/absolute/path/accepted-packages", packages)
    results.append(run("owner handoff block", owner, root))
    results.append(run("step 1 start folder (without launching claude)", start_block.replace(" && claude", ""), home))
    r = run("prompt step 1", sub(steps["1"]), project); results.append(r)
    asserts["step1LastStdoutLineIs120"] = r["exit"] == 0 and r["stdout"][-1:] == ["1.2.0"]
    r = run("step 3 token block", sub(token_block), project, stdin=token + "\n"); results.append(r)
    asserts["tokenBlockExitZeroAndTokenNotEchoed"] = r["exit"] == 0 and "<token>" not in json.dumps(r)
    r = run("prompt step 3", sub(steps["3"]), project); results.append(r)
    current = r["_full"]
    asserts["step3ShowsUrlTenantActorTokenMasked"] = (r["exit"] == 0 and "http://127.0.0.1:18170" in current and values["TENANT"] in current
                                                       and values["ACTOR"] in current and "***" in current and "<token>" not in current)
    r = run("prompt step 4", sub(steps["4"]), project); results.append(r)
    asserts["step4Connected"] = r["exit"] == 0 and any("Connected" in line for line in r["stdout"])
    r = run("step 5 teardown block", teardown_block, project); results.append(r)
    asserts["step5RemovesRegistrationAndFolder"] = r["exit"] == 0 and not os.path.exists(os.path.join(home, "hexalith-operator"))
finally:
    report = {"readmeSha256": hashlib.sha256(raw).hexdigest(), "gatewayCalls": 0,
              "note": "Commands extracted from the README and run in fresh bash shells under a scratch HOME; token piped into the masked read, never printed. The task environment had been removed, so no Gateway query ran.",
              "assertions": asserts, "allAssertionsPass": bool(asserts) and all(asserts.values()) and len(asserts) == 5, "results": results}
    for x in results:
        x.pop("_full", None)
    json.dump(report, open(output, "w"), indent=2)
    shutil.rmtree(root, ignore_errors=True)
print(json.dumps({"readmeSha256": report["readmeSha256"], "assertions": asserts}, indent=1))
