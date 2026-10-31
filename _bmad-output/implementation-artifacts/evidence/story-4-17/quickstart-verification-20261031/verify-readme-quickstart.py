"""Run the README quick-start commands verbatim (placeholders substituted) in fresh shells under a scratch HOME.

Usage: verify-readme-quickstart.py <readme> <scratch-root> <accepted-packages> <protected-profile> <output-json>
The token is piped from the protected profile into the README's masked read; it is never printed.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

readme, root, packages, protected, output = sys.argv[1:6]
text = open(readme, encoding="utf-8").read()
section = text.split("### Quick start: Claude Code sets it up for you\n", 1)[1].split("### Install into an isolated directory\n", 1)[0]
blocks = re.findall(r"```(\w*)\n(.*?)```", section, re.S)
start_block = next(b for lang, b in blocks if lang == "sh" and "claude" in b and "mkdir -p" in b)
prompt = next(b for lang, b in blocks if lang == "text" and b.startswith("Set up the Hexalith MCP server"))
token_block = next(b for lang, b in blocks if lang == "sh" and "read -rsp" in b)
owner_block = next(b for lang, b in blocks if lang == "sh" and "handoff=/absolute/path/handoff" in b)
task_prompt = next(b for lang, b in blocks if lang == "text" and b.startswith("Use only the hexalith MCP tools"))
steps = {m.group(1): m.group(2) for m in re.finditer(r"^(\d)\. (.+)$", prompt, re.M)}

home = os.path.join(root, "home")
handoff = os.path.join(root, "handoff")
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


def run(label, command, cwd, stdin=None):
    proc = subprocess.run(["bash", "-c", command], cwd=cwd, env=env, input=stdin, capture_output=True, text=True, timeout=240)
    out = (proc.stdout + proc.stderr).replace(root, "<root>").replace(token, "<token>")
    return {"label": label, "exit": proc.returncode, "tail": out.strip().splitlines()[-12:]}


results = []
owner = owner_block.replace("/absolute/path/handoff", handoff).replace("/absolute/path/accepted-packages", packages)
results.append(run("owner handoff block", owner, root))
results.append(run("start folder (without launching claude)", start_block.replace(" && claude", ""), home))
project = os.path.join(home, "hexalith-operator", "project")
results.append(run("prompt step 1", sub(steps["1"]), project))
results.append(run("README token block", sub(token_block), project, stdin=token + "\n"))
results.append(run("prompt step 3", sub(steps["3"]), project))
results.append(run("prompt step 4", sub(steps["4"]), project))
results.append(run("supplemental read-only tenant query",
                   'export DOTNET_ROOT="$(dirname "$(readlink -f "$(command -v dotnet)")")" MCPCLI_HOME="$HOME/hexalith-operator/home" && "$HOME/hexalith-operator/tools/hexalith" query tenants.get-tenant --profile operator --payload \'{"TenantId":"mcpcli-417-20261031-155f9b6d"}\' 2>/dev/null | python3 -I -c \'import json,sys; d=json.load(sys.stdin); print(d["tenant"], d["document"]["tenantId"], d["document"]["status"])\'',
                   project))
results.append(run("cleanup registration", "claude mcp remove hexalith -s local", project))
report = {"readmeSha256": hashlib.sha256(open(readme, "rb").read()).hexdigest(),
          "taskPromptPlaceholders": sorted(set(re.findall(r"\b(TENANT|PARTY-ID)\b", task_prompt))),
          "domainCalls": "one read-only tenants.get-tenant query; no command", "results": results}
json.dump(report, open(output, "w"), indent=2)
print(json.dumps(report, indent=1))
