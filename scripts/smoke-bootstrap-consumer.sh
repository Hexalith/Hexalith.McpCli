#!/usr/bin/env bash
set -euo pipefail

release_version="${1:?Release version is required}"
package_source="${2:?Package source is required}"
consumer_directory="${3:?Fresh consumer directory is required}"
python3 scripts/release-request.py "$release_version" bootstrap
package_source="$(python3 - "$package_source" <<'PY'
from pathlib import Path
import sys
from urllib.parse import urlsplit

source = sys.argv[1]
print(source if urlsplit(source).scheme in ('http', 'https') else Path(source).resolve())
PY
)"
consumer_directory="$(realpath -m "$consumer_directory")"
mkdir "$consumer_directory"
cp global.json "$consumer_directory/global.json"
python3 - "$consumer_directory/NuGet.Config" "$package_source" <<'PY'
import sys
from xml.etree import ElementTree

configuration = ElementTree.Element("configuration")
sources = ElementTree.SubElement(configuration, "packageSources")
ElementTree.SubElement(sources, "clear")
ElementTree.SubElement(sources, "add", key="verified", value=sys.argv[2])
fallback = ElementTree.SubElement(configuration, "fallbackPackageFolders")
ElementTree.SubElement(fallback, "clear")
ElementTree.ElementTree(configuration).write(sys.argv[1], encoding="utf-8", xml_declaration=True)
PY
cat > "$consumer_directory/Bootstrap.Consumer.Contracts.csproj" <<EOF
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup>
  <ItemGroup><PackageReference Include="Hexalith.McpCli.Abstractions" Version="[$release_version]" /></ItemGroup>
</Project>
EOF
cat > "$consumer_directory/Module.cs" <<'EOF'
using Hexalith.McpCli.Abstractions;
[assembly: HexalithModule("sample", "Consumer sample", IdentifierKind.Ulid)]
EOF
cat > "$consumer_directory/CreateItemCommand.cs" <<'EOF'
using Hexalith.McpCli.Abstractions;
[HexalithCommand("Create a sample item.", Domain = "sample", WireType = "create-item", AggregateIdProperty = nameof(Id))]
public sealed record CreateItemCommand([property: HexalithIdentifier] string Id);
EOF
cat > "$consumer_directory/GetItemQuery.cs" <<'EOF'
using Hexalith.McpCli.Abstractions;
[HexalithQuery("Read a sample item.", Domain = "sample", WireType = "get-item", AggregateIdProperty = nameof(Id), ProjectionType = "items")]
public sealed record GetItemQuery([property: HexalithIdentifier] string Id);
EOF
cat > "$consumer_directory/MissingDescriptionQuery.cs" <<'EOF'
using Hexalith.McpCli.Abstractions;
[HexalithQuery(" ")]
public sealed record MissingDescriptionQuery;
EOF
export NUGET_PACKAGES="$consumer_directory/packages"
export NUGET_FALLBACK_PACKAGES=""
export NUGET_HTTP_CACHE_PATH="$consumer_directory/http-cache"
export DOTNET_CLI_UI_LANGUAGE=en
consumer_properties=(
  "-p:RestoreSources=$package_source" "-p:RestorePackagesPath=$consumer_directory/packages"
  -p:RestoreAdditionalProjectSources= -p:RestoreFallbackFolders= -p:RestoreAdditionalProjectFallbackFolders=
  -p:ImportDirectoryBuildProps=false -p:ImportDirectoryBuildTargets=false -p:ImportDirectoryPackagesProps=false
)
dotnet restore "$consumer_directory/Bootstrap.Consumer.Contracts.csproj" \
  --configfile "$consumer_directory/NuGet.Config" --no-cache \
  "${consumer_properties[@]}"
dotnet build "$consumer_directory/Bootstrap.Consumer.Contracts.csproj" --configuration Release --no-restore \
  "${consumer_properties[@]}" 2>&1 | tee "$consumer_directory/build.log"
grep -q 'warning MCPCLI001:' "$consumer_directory/build.log"
grep -Eq '^[[:space:]]*1 Warning\(s\)$' "$consumer_directory/build.log"
if grep -Eq 'CS8032|CS9057' "$consumer_directory/build.log"; then
  echo "The packaged analyzer could not load in the consumer." >&2
  exit 1
fi
