#!/usr/bin/env bash
# Verify the README quick-start commands verbatim, under a scratch HOME, with the accepted local packages.
# Usage: verify-quickstart.sh <scratch-root> <accepted-packages-dir> <protected-profile-json>
set -uo pipefail
root=$1 packages=$2 protected=$3
export HOME="$root/home"
mkdir -p "$HOME"
handoff="$root/handoff"
step() { printf '\n== %s\n' "$*"; }

step "owner: prepare handoff folder"
mkdir "$handoff"
cp "$packages"/*.nupkg "$handoff"/
cat > "$handoff/NuGet.Config" <<EOF
<configuration>
  <packageSources>
    <clear />
    <add key="accepted-local" value="$handoff" />
  </packageSources>
  <fallbackPackageFolders><clear /></fallbackPackageFolders>
</configuration>
EOF
sha256sum "$handoff"/*.nupkg | sed "s#$root#<root>#"

step "1. start folder"
mkdir -p ~/hexalith-operator/project && cd ~/hexalith-operator/project && pwd | sed "s#$root#<root>#"

step "prompt step 1: install"
export NUGET_PACKAGES="$HOME/hexalith-operator/packages" && dotnet tool install Hexalith.McpCli --version 1.2.0 --tool-path "$HOME/hexalith-operator/tools" --configfile "$handoff/NuGet.Config" --no-cache && "$HOME/hexalith-operator/tools/hexalith" --version
echo "exit=$?"

step "token command (token piped from the protected profile; never printed)"
export MCPCLI_HOME="$HOME/hexalith-operator/home"
python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"]["operator"]["token"])' "$protected" | {
  read -rsp 'Token: ' token && echo && "$HOME/hexalith-operator/tools/hexalith" config profile add operator --url http://127.0.0.1:18170 --token "$token"; unset token
}
echo "exit=$?"

step "prompt step 3: tenant, actor, current"
"$HOME/hexalith-operator/tools/hexalith" config set operator tenant mcpcli-417-20261031-155f9b6d; echo "exit=$?"
"$HOME/hexalith-operator/tools/hexalith" config set operator actor mcpcli-417-operator-20261031-155f9b6d; echo "exit=$?"
"$HOME/hexalith-operator/tools/hexalith" config current --profile operator; echo "exit=$?"

step "prompt step 4: register and show"
claude mcp add --transport stdio --scope local --env MCPCLI_HOME="$HOME/hexalith-operator/home" hexalith -- "$HOME/hexalith-operator/tools/hexalith" mcp --transport stdio --profile operator 2>&1 | sed "s#$root#<root>#g"; echo "exit=${PIPESTATUS[0]}"
claude mcp get hexalith 2>&1 | sed "s#$root#<root>#g"; echo "exit=${PIPESTATUS[0]}"

step "supplemental read-only check of the stored token (one tenants.get-tenant query)"
"$HOME/hexalith-operator/tools/hexalith" query tenants.get-tenant --profile operator --payload '{"TenantId":"mcpcli-417-20261031-155f9b6d"}' | python3 -I -c 'import json,sys; d=json.load(sys.stdin); print({"tenant": d.get("tenant"), "tenantId": d.get("document",{}).get("tenantId"), "status": d.get("document",{}).get("status")})'
echo "exit=${PIPESTATUS[0]}"

step "registered command for the init probe"
python3 -I -c 'import json,os,sys; c=json.load(open(os.path.expanduser("~/.claude.json"))); p=c["projects"][os.getcwd()]["mcpServers"]["hexalith"]; print(json.dumps({"command": p["command"], "args": p["args"], "env": sorted(p.get("env",{}))}))' | sed "s#$root#<root>#g"
