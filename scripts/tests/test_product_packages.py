"""Preserve package payload and analyzer-consumer assertions without release orchestration."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
import sys
import tempfile
import unittest
import warnings
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import product_packages

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "Hexalith.McpCli.Abstractions.1.0.0.nupkg"
SHA = "d9f822d64f7afa9bd51ca1698f5051147b86b554"


def package(path, *, identity="Hexalith.McpCli.Abstractions", version="1.0.0", missing=(), dependency=False,
            core_properties=None, framework="net11.0"):
    files = {
        "Hexalith.McpCli.Abstractions.nuspec": (
            f'<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"><metadata>'
            f'<id>{identity}</id><version>{version}</version><repository type="git" commit="{SHA}" />'
            + ('<dependencies><group><dependency id="Leak" version="1.0.0" /></group></dependencies>' if dependency else '')
            + '</metadata></package>'
        ),
        f"lib/{framework}/Hexalith.McpCli.Abstractions.dll": "compile fixture",
        "analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll": "analyzer fixture",
    }
    if core_properties is not None:
        files["package/services/metadata/core-properties/nuget.psmdcp"] = core_properties
    with ZipFile(path, "w") as archive:
        for name, contents in files.items():
            if name not in missing:
                archive.writestr(name, contents)


class ProductPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        (self.root / "tools").mkdir()
        shutil.copy(ROOT / "tools/release-packages.json", self.root / "tools/release-packages.json")
        shutil.copy(ROOT / "global.json", self.root / "global.json")
        self.bin = self.root / "stubs"
        self.bin.mkdir()
        self.env = dict(os.environ, LC_ALL="C", PATH=f"{self.bin}:{os.environ['PATH']}",
                        RELEASE_TEST_ROOT=str(self.root), NUGET_API_KEY="fixture-secret-never-print")
        self.executable("dotnet", '''#!/usr/bin/env python3
import hashlib, json, os, sys
from pathlib import Path
from zipfile import ZipFile
root = Path(os.environ["RELEASE_TEST_ROOT"])
args = sys.argv[1:]
safe = ["REDACTED" if i and args[i-1] == "--api-key" else arg for i, arg in enumerate(args)]
with (root / "dotnet.log").open("a") as log: log.write(json.dumps(safe) + "\\n")
if args[0] == "msbuild":
    project = args[1]
    print(json.dumps({"Properties": {"TargetFramework": os.environ.get("SOURCE_FRAMEWORK", "net11.0"), "TargetFrameworks": os.environ.get("SOURCE_FRAMEWORKS", ""), "PackAsTool": "true", "ToolCommandName": "hexalith", "UseAppHost": "false", "PublishTrimmed": "false", "PublishAot": "false", "PublishReadyToRun": "false", "SelfContained": "false", "RuntimeIdentifier": "", "RuntimeIdentifiers": "", "CreateRidSpecificToolPackages": "false", "PackageId": Path(project).stem, "Version": "1.0.0"}}))
    sys.exit(0)
if args[0] in ("restore", "build") and args[1] == "src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj":
    if os.environ.get(args[0].upper() + "_FAIL"):
        print("fixture production " + args[0] + " failed", file=sys.stderr)
        sys.exit(1)
if args[0] == "pack":
    if os.environ.get("PACK_FAIL"): sys.exit(1)
    directory = Path(args[args.index("--output") + 1])
    version = next(arg.split("=", 1)[1] for arg in args if arg.startswith("-p:Version="))
    dependencies = '<dependencies><dependency id="Leak" version="1.0.0" /></dependencies>' if os.environ.get("PACK_INVALID") == "dependency" else ''
    with ZipFile(directory / f"Hexalith.McpCli.Abstractions.{version}.nupkg", "w") as archive:
        archive.writestr("Abstractions.nuspec", f"<package><metadata><id>Hexalith.McpCli.Abstractions</id><version>{version}</version>{dependencies}</metadata></package>")
        archive.writestr("lib/" + os.environ.get("SOURCE_FRAMEWORK", "net11.0") + "/Hexalith.McpCli.Abstractions.dll", "compile fixture")
        archive.writestr("analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll", "analyzer fixture")
    if os.environ.get("PACK_INVALID") == "symbols":
        (directory / "symbols.snupkg").write_bytes(b"unexpected symbols")
    if os.environ.get("AFTER_PACK_SOURCE_STATE"):
        (root / "local-source-state").write_text(os.environ["AFTER_PACK_SOURCE_STATE"])
if "Bootstrap.Consumer.Contracts.csproj" in args[1]:
    (root / "consumer-environment.json").write_text(json.dumps({name: os.environ.get(name) for name in
        ("NUGET_PACKAGES", "NUGET_FALLBACK_PACKAGES", "NUGET_HTTP_CACHE_PATH")}))
    if os.environ.get("SMOKE_FAIL"): sys.exit(1)
    if args[0] == "restore":
        (root / "consumer-nuget.config").write_text(Path(args[args.index("--configfile") + 1]).read_text())
    if args[0] == "build":
        if os.environ.get("AFTER_CONSUMER_SOURCE_STATE"):
            (root / "local-source-state").write_text(os.environ["AFTER_CONSUMER_SOURCE_STATE"])
        if os.environ.get("SMOKE_MUTATE_PACKAGE"):
            with ZipFile(root / "nupkgs/bootstrap/Hexalith.McpCli.Abstractions.1.0.0.nupkg", "a") as archive:
                archive.writestr("changed-during-consumer.txt", "bytes the restore did not consume")
        diagnostic = "MissingDescriptionQuery.cs(2,1): warning MCPCLI001: fixture"
        print({"missing-diagnostic": "    1 Warning(s)",
               "wrong-file": "CreateItemCommand.cs(2,1): warning MCPCLI001: fixture\\n    1 Warning(s)",
               "split-diagnostic": "MissingDescriptionQuery.cs(2,\\n1): warning MCPCLI001: fixture\\n    1 Warning(s)",
               "extra-warning": diagnostic + "\\n    2 Warning(s)",
               "load-failure": "warning CS8032: fixture\\n    1 Warning(s)",
               "newer-analyzer": "warning CS9057: fixture\\n    1 Warning(s)"}
              .get(os.environ.get("SMOKE_OUTPUT"), diagnostic + "\\n    1 Warning(s)"))
if args[:2] == ["nuget", "push"]:
    if os.environ.get("EXPECTED_PUBLICATION_KEY") and args[args.index("--api-key") + 1] != os.environ["EXPECTED_PUBLICATION_KEY"]:
        print("The publication key did not come from the NuGet login output.", file=sys.stderr)
        sys.exit(1)
    if os.environ.get("PUSH_FAIL"):
        print("fixture NuGet push failed: HTTP 403", file=sys.stderr)
        sys.exit(43)
    package = Path(args[2])
    (root / "pushed.sha256").write_text(hashlib.sha256(package.read_bytes()).hexdigest())
    (root / "pushed.path").write_text(str(package))
''')

    def executable(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def run_script(self, script, *args):
        command = ["python3" if script.endswith(".py") else "bash", f"scripts/{script}", *args]
        result = subprocess.run(command, cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertNotIn("fixture-secret-never-print", result.stdout + result.stderr)
        return result

    def calls(self):
        path = self.root / "dotnet.log"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def assert_no_push(self):
        self.assertFalse(any(call[:2] == ["nuget", "push"] for call in self.calls()))

    def staged(self, **options):
        staging = self.root / "nupkgs/bootstrap"
        staging.mkdir(parents=True, exist_ok=True)
        path = staging / PACKAGE
        package(path, **options)
        self.write_receipt(path)
        return path

    def write_receipt(self, path, **overrides):
        receipt = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "source_sha": SHA, "source_clean": True}
        receipt.update(overrides)
        (path.parent.parent / "bootstrap.sha256").write_text(json.dumps(receipt) + "\n")

    def paired_tool(self, *, missing=(), package_type=True, command=None, manifest='("Sample.Contracts", "Sample.Contracts")', assembly=True):
        prefix = "tools/net11.0/any/"
        managed = bytearray(640)
        managed[:2] = b'MZ'
        struct.pack_into('<I', managed, 0x3c, 64)
        managed[64:68] = b'PE\0\0'
        struct.pack_into('<H', managed, 88, 0x10b)
        struct.pack_into('<H', managed, 64 + 6, 1)
        struct.pack_into('<H', managed, 64 + 20, 224)
        struct.pack_into('<II', managed, 88 + 96 + 14 * 8, 0x2000, 72)
        struct.pack_into('<IIII', managed, 312 + 8, 256, 0x2000, 256, 384)
        struct.pack_into('<I', managed, 384, 72)
        struct.pack_into('<I', managed, 384 + 16, 1)
        struct.pack_into('<II', managed, 384 + 8, 0x2050, 68)
        metadata = 464
        managed[metadata:metadata + 4] = b'BSJB'
        struct.pack_into('<HHII', managed, metadata + 4, 1, 1, 0, 12)
        managed[metadata + 16:metadata + 28] = b'v4.0.30319\0\0'
        struct.pack_into('<HHII', managed, metadata + 28, 0, 1, 44, 24)
        managed[metadata + 40:metadata + 44] = b'#~\0\0'
        managed[metadata + 48:metadata + 52] = bytes([2, 0, 0, 1])
        files = {
            "Hexalith.McpCli.nuspec": f'<package><metadata><id>Hexalith.McpCli</id><version>1.0.0</version><repository type="git" commit="{SHA}" />'
                + ('<packageTypes><packageType name="DotnetTool" /></packageTypes>' if package_type else '')
                + '</metadata></package>',
            "README.md": "fixture", prefix + "Hexalith.McpCli.dll": bytes(managed),
            prefix + "Hexalith.McpCli.deps.json": json.dumps({"runtimeTarget": {"name": ".NETCoreApp,Version=v11.0"}, "libraries": {"Sample.Contracts/1.0.0": {}}, "targets": {".NETCoreApp,Version=v11.0": {"Sample.Contracts/1.0.0": {}}}}),
            prefix + "Hexalith.McpCli.runtimeconfig.json": json.dumps({"runtimeOptions": {"tfm": "net11.0", "framework": {"name": "Microsoft.NETCore.App", "version": "11.0.0"}}}),
            prefix + "DotnetToolSettings.xml": '<DotNetCliTool><Commands><Command '
                + (command if command is not None else 'Name="hexalith" EntryPoint="Hexalith.McpCli.dll" Runner="dotnet"')
                + ' /></Commands></DotNetCliTool>',
        }
        project = self.root / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        project.parent.mkdir(parents=True, exist_ok=True)
        project.write_text('<Project><ItemGroup><PackageReference Include="Sample.Contracts" HexalithContracts="true" /></ItemGroup></Project>')
        assets = project.parent / 'obj/project.assets.json'
        assets.parent.mkdir(parents=True, exist_ok=True)
        assets.write_text(json.dumps({'libraries': {'Sample.Contracts/1.0.0': {}}}))
        (self.root / 'tools/dependency-policy.json').write_text(json.dumps({'modules': {'Sample.Contracts': '1.0.0'}}))
        if assembly:
            files[prefix + "Sample.Contracts.dll"] = bytes(managed)
        with ZipFile(self.root / "nupkgs/bootstrap/Hexalith.McpCli.1.0.0.nupkg", "w") as archive:
            for name, contents in files.items():
                if name not in missing:
                    archive.writestr(name, contents)
        path = self.root / "src/Hexalith.McpCli/obj/Release/net11.0/ModuleAssemblyManifest.g.cs"
        path.parent.mkdir(parents=True, exist_ok=True)
        if manifest is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(manifest)

    def test_invalid_package_matrix_is_rejected_by_product_validation(self):
        cases = (
            ({"identity": "Wrong"}, "Unexpected package ID"),
            ({"version": "2.0.0"}, "Unexpected package version"),
            ({"missing": ("lib/net11.0/Hexalith.McpCli.Abstractions.dll",)}, "compile DLL"),
            ({"missing": ("analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll",)}, "analyzer DLL"),
            ({"dependency": True}, "consumer-visible package dependencies"),
            ({"missing": ("Hexalith.McpCli.Abstractions.nuspec",)}, "one nuspec"),
        )
        for options, message in cases:
            with self.subTest(options=options):
                path = self.staged(**options)
                result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()

    def test_extra_artifacts_and_symbol_packages_are_rejected_by_product_validation(self):
        path = self.staged()
        for name in ("Unexpected.1.0.0.nupkg", "symbols.snupkg", "extra.txt", "subdirectory"):
            with self.subTest(name=name):
                extra = path.parent / name
                if name == "subdirectory": extra.mkdir()
                else: extra.write_text("unexpected")
                result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Expected", result.stderr)
                self.assert_no_push()
                if extra.is_dir(): extra.rmdir()
                else: extra.unlink()

    def test_duplicate_archive_entries_and_symlink_packages_are_rejected_by_product_validation(self):
        path = self.staged()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(path, "a") as archive:
                archive.writestr("lib/net11.0/Hexalith.McpCli.Abstractions.dll", "duplicate")
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate archive entries", result.stderr)
        path.unlink()
        outside = self.root / "outside.nupkg"
        package(outside)
        path.symlink_to(outside)
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular package file", result.stderr)
        self.assert_no_push()

    def test_missing_package_and_malformed_archives_are_rejected_by_product_validation(self):
        path = self.staged()
        path.unlink()
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected", result.stderr)
        path.write_text("not a zip")
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a zip", result.stderr)
        self.staged()
        with ZipFile(path, "a") as archive: archive.writestr("other.nuspec", "<package />")
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("one nuspec", result.stderr)
        self.assert_no_push()

    def test_analyzer_diagnostic_rejections_propagate_from_the_product_consumer(self):
        for output, message in (("missing-diagnostic", "did not report MCPCLI001 on MissingDescriptionQuery.cs"),
                                ("wrong-file", "did not report MCPCLI001 on MissingDescriptionQuery.cs"),
                                ("split-diagnostic", "did not report MCPCLI001 on MissingDescriptionQuery.cs"),
                                ("extra-warning", "must report exactly one warning"),
                                ("load-failure", "packaged analyzer could not load"),
                                ("newer-analyzer", "packaged analyzer could not load")):
            with self.subTest(output=output):
                self.env["SMOKE_OUTPUT"] = output
                result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", "consumer-" + output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()

    def test_consumer_failure_propagates_without_release_orchestration(self):
        self.env["SMOKE_FAIL"] = "1"
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", "consumer")
        self.assertNotEqual(result.returncode, 0)
        self.assert_no_push()

    def test_product_receipt_rejects_package_mutation_during_consumer_build_and_symlink_receipts(self):
        path = self.staged()
        self.paired_tool()
        receipt = self.root / 'prepared.json'
        document = {'schema': 'mcpcli-product-packages/v1', 'source_sha': SHA, 'version': '1.0.0',
                    'packages': product_packages.packages(path.parent, '1.0.0')}
        receipt.write_text(json.dumps(document))
        product_packages.check_prepared(path.parent, receipt)
        self.env['SMOKE_MUTATE_PACKAGE'] = '1'
        result = self.run_script('smoke-bootstrap-consumer.sh', '1.0.0', str(path.parent), 'consumer')
        self.assertEqual(0, result.returncode, result.stderr)
        with self.assertRaisesRegex(ValueError, 'does not bind'):
            product_packages.check_prepared(path.parent, receipt)
        self.staged()
        actual = receipt.with_name('actual.json')
        receipt.rename(actual)
        receipt.symlink_to(actual)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            product_packages.check_prepared(path.parent, receipt)
        self.assert_no_push()

    def test_paired_validation_rejects_unsafe_archive_members(self):
        self.staged()
        self.paired_tool()
        tool = self.root / 'nupkgs/bootstrap/Hexalith.McpCli.1.0.0.nupkg'
        original = tool.read_bytes()
        for member in ('../escape.txt', '/absolute.txt', 'tools\\escape.txt'):
            tool.write_bytes(original)
            with ZipFile(tool, 'a') as archive: archive.writestr(member, 'unexpected')
            result = self.run_script('validate-release-packages.py', str(tool.parent), '1.0.0', 'paired', '--source-sha', SHA)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Unsafe archive entry', result.stderr)
            self.assert_no_push()

    def test_paired_validation_keeps_existing_tool_structure_checks(self):
        path = self.staged()
        prefix = "tools/net11.0/any/"
        cases = [({"missing": (name,)}, "tool package is missing") for name in
                 ("README.md", prefix + "DotnetToolSettings.xml", prefix + "Hexalith.McpCli.dll",
                  prefix + "Hexalith.McpCli.deps.json", prefix + "Hexalith.McpCli.runtimeconfig.json")]
        cases += [({"package_type": False}, "not marked as a .NET tool"),
                  ({"command": 'Name="other" EntryPoint="Hexalith.McpCli.dll" Runner="dotnet"'}, "command is not hexalith"),
                  ({"command": 'Name="hexalith" EntryPoint="other.dll" Runner="dotnet"'}, "command is not hexalith"),
                  ({"command": 'Name="hexalith" EntryPoint="Hexalith.McpCli.dll" Runner="other"'}, "command is not hexalith"),
                  ({"manifest": None}, "manifest is missing"),
                  ({"manifest": "// empty"}, "no enrolled Contracts assemblies"),
                  ({"manifest": '("Wrong", "Sample.Contracts")'}, "Invalid Contracts assembly manifest entry"),
                  ({"manifest": '("Sample.Contracts", "Wrong")'}, "Invalid Contracts assembly manifest entry"),
                  ({"assembly": False}, "missing Sample.Contracts.dll")]
        for options, message in cases:
            with self.subTest(options=options):
                self.paired_tool(**options)
                result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "paired", "--source-sha", SHA)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()
        self.paired_tool()
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "paired", "--source-sha", SHA)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_no_push()

    def test_paired_validator_rejects_runtime_and_enrollment_drift(self):
        self.staged()
        prefix = 'tools/net11.0/any/'
        cases = [
            (prefix + 'Hexalith.McpCli.dll', b'native payload', 'managed PE'),
            (prefix + 'Hexalith.McpCli.deps.json', json.dumps({'runtimeTarget': {'name': '.NETCoreApp,Version=v11.0/linux-x64'}}), 'portable .NET 11'),
            (prefix + 'Hexalith.McpCli.deps.json', json.dumps({'runtimeTarget': {'name': '.NETCoreApp,Version=v11.0'}, 'libraries': {}}), 'Packaged Contracts versions'),
            (prefix + 'Hexalith.McpCli.runtimeconfig.json', json.dumps({'runtimeOptions': {'tfm': 'net11.0', 'includedFrameworks': [{'name': 'Microsoft.NETCore.App'}]}}), 'framework-dependent'),
        ]
        path = self.root / 'nupkgs/bootstrap/Hexalith.McpCli.1.0.0.nupkg'
        for name, payload, message in cases:
            with self.subTest(name=name, message=message):
                self.paired_tool()
                with ZipFile(path) as archive:
                    files = {item: archive.read(item) for item in archive.namelist()}
                files[name] = payload
                with ZipFile(path, 'w') as archive:
                    for item, contents in files.items(): archive.writestr(item, contents)
                result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired', '--source-sha', SHA)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()
        self.paired_tool()
        (self.root / 'tools/dependency-policy.json').write_text(json.dumps({'modules': {'Sample.Contracts': '2.0.0'}}))
        result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired', '--source-sha', SHA)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Restored Contracts versions', result.stderr)
        self.paired_tool()
        (self.root / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj').write_text('<Project />')
        result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired', '--source-sha', SHA)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Generated manifest, flagged Contracts references', result.stderr)
        self.assert_no_push()

    def test_paired_validator_refuses_native_files_and_native_dependency_entries(self):
        self.staged()
        self.paired_tool()
        prefix = 'tools/net11.0/any/'
        path = self.root / 'nupkgs/bootstrap/Hexalith.McpCli.1.0.0.nupkg'
        with ZipFile(path) as archive:
            base = {name: archive.read(name) for name in archive.namelist()}
        mixed = bytearray(base[prefix + 'Hexalith.McpCli.dll'])
        struct.pack_into('<I', mixed, 384 + 16, 0)
        precompiled = bytearray(base[prefix + 'Hexalith.McpCli.dll'])
        struct.pack_into('<II', precompiled, 384 + 64, 1, 1)
        native_dll = bytearray(base[prefix + 'Hexalith.McpCli.dll'])
        struct.pack_into('<II', native_dll, 88 + 96 + 14 * 8, 0, 0)
        bit32 = bytearray(base[prefix + 'Hexalith.McpCli.dll'])
        struct.pack_into('<I', bit32, 384 + 16, 3)
        cases = [(prefix + name, payload, message) for name, payload, message in [
            ('libextra.so', b'native', 'Native payload'), ('libextra.so.1.2', b'native', 'Native payload'),
            ('libextra.dylib', b'native', 'Native payload'), ('arbitrary-host.exe', b'native', 'Native payload'),
            ('payload.bin', b'\x7fELF' + bytes(12), 'Native payload'),
            ('mach.bin', b'\xcf\xfa\xed\xfe' + bytes(12), 'Native payload'),
            ('archive.bin', b'!<arch>\n' + bytes(12), 'Native payload'),
            ('native.dll', bytes(native_dll), 'no managed CLR header'),
            ('mixed.dll', bytes(mixed), 'portable managed IL'),
            ('precompiled.dll', bytes(precompiled), 'portable managed IL'),
            ('x86.dll', bytes(bit32), 'portable managed IL'),
        ]]
        for label, offset, value, message in [
            ('unknown-magic', 88, struct.pack('<H', 0x9999), 'managed PE'),
            ('missing-metadata', 384 + 8, bytes(8), 'metadata'),
            ('unmapped-metadata', 384 + 8, struct.pack('<II', 0x3000, 64), 'metadata'),
            ('truncated-metadata', 384 + 8, struct.pack('<II', 0x20f0, 64), 'metadata'),
            ('invalid-signature', 464, b'FAKE', 'metadata root'),
            ('invalid-version', 464 + 12, struct.pack('<I', 1000), 'metadata version'),
            ('invalid-stream', 464 + 32, struct.pack('<I', 1000), 'metadata stream'),
        ]:
            payload = bytearray(base[prefix + 'Hexalith.McpCli.dll'])
            payload[offset:offset + len(value)] = value
            if label == 'unknown-magic':
                # The old parser used the optional header itself as the directory fallback.
                struct.pack_into('<II', payload, 88 + 14 * 8, 0x2000, 72)
                struct.pack_into('<II', payload, 88 + 112 + 14 * 8, 0x2000, 72)
            cases.append((prefix + label + '.dll', bytes(payload), message))
        cases.extend([
            ('tools/net11.0/win-x64/payload.exe', b'MZnative', 'Alternate tools layouts'),
            ('tools/net9.0/any/readme.txt', b'alternate', 'Alternate tools layouts'),
            ('tools/net10.0/any/readme.txt', b'previous framework', 'Alternate tools layouts'),
            ('content/native-host.bin', b'MZnative', 'executable payload'),
            ('content/native.exe', b'native', 'Native payload'),
            ('content/libnative.so', b'native', 'Native payload'),
            ('content/elf.bin', b'\x7fELF' + bytes(12), 'Native payload'),
        ])
        for kind, assets in [('native', {'extra.so': {}}),
                             ('runtimeTargets', {'runtimes/linux-x64/native/extra.so': {'assetType': 'native', 'rid': 'linux-x64'}})]:
            deps = json.loads(base[prefix + 'Hexalith.McpCli.deps.json'])
            deps['targets']['.NETCoreApp,Version=v11.0']['Sample.Contracts/1.0.0'][kind] = assets
            cases.append((prefix + 'Hexalith.McpCli.deps.json', json.dumps(deps), 'Native'))
        for name, payload, message in cases:
            with self.subTest(name=name, message=message):
                with ZipFile(path, 'w') as archive:
                    files = {**base, name: payload}
                    for item, contents in files.items(): archive.writestr(item, contents)
                result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired', '--source-sha', SHA)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()

    def test_paired_validator_binds_both_nuspec_commits_and_never_receipts_failure(self):
        path = self.staged()
        self.paired_tool()
        paths = [path, path.with_name('Hexalith.McpCli.1.0.0.nupkg')]
        def repository_commit(package_path, commit):
            with ZipFile(package_path) as archive:
                files = {name: archive.read(name) for name in archive.namelist()}
            nuspec = next(name for name in files if name.endswith('.nuspec'))
            from xml.etree import ElementTree
            root = ElementTree.fromstring(files[nuspec])
            metadata = root.find('{*}metadata')
            for item in metadata.findall('{*}repository'):
                metadata.remove(item)
            if commit is not None:
                ElementTree.SubElement(metadata, 'repository', type='git', commit=commit)
            files[nuspec] = ElementTree.tostring(root)
            with ZipFile(package_path, 'w') as archive:
                for name, value in files.items(): archive.writestr(name, value)
        for package_path in paths:
            repository_commit(package_path, SHA)
        output = self.root / 'validated.json'
        result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired',
                                 '--output', str(output))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires --source-sha', result.stderr)
        self.assertFalse(output.exists())
        result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired',
                                 '--source-sha', SHA, '--output', str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(output.read_text())
        self.assertEqual(receipt['source_sha'], SHA)
        self.assertEqual(receipt['phase'], 'paired')
        self.assertEqual(receipt['packages'], {item.name: hashlib.sha256(item.read_bytes()).hexdigest() for item in paths})
        output.unlink()
        for package_path in paths:
            for commit in (None, 'b' * 40):
                with self.subTest(package=package_path.name, commit=commit):
                    repository_commit(package_path, commit)
                    result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired',
                                             '--source-sha', SHA, '--output', str(output))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('repository commit differs', result.stderr)
                    self.assertFalse(output.exists())
                    repository_commit(package_path, SHA)
        self.assert_no_push()

    def test_validator_rejects_changed_package_manifest_unknown_phase_and_invalid_version(self):
        path = self.staged()
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid release version: 1.0", result.stderr)
        self.assert_no_push()
        manifest = self.root / "tools/release-packages.json"
        original = manifest.read_text()
        packages = json.loads(original)
        packages["packages"].reverse()
        manifest.write_text(json.dumps(packages))
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release manifest must declare exactly the paired package IDs", result.stderr)
        self.assert_no_push()
        manifest.write_text(original)
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown release phase: unknown", result.stderr)
        self.assert_no_push()

    def test_bootstrap_framework_and_consumer_follow_effective_source(self):
        from xml.etree import ElementTree
        for framework in ("net10.0", "net11.0"):
            with self.subTest(framework=framework):
                self.env["SOURCE_FRAMEWORK"] = framework
                staged = self.staged(framework=framework)
                result = self.run_script("validate-release-packages.py", str(staged.parent), "1.0.0", "bootstrap")
                self.assertEqual(result.returncode, 0, result.stderr)
                consumer = self.root / ("consumer-" + framework)
                result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", str(staged.parent), str(consumer))
                self.assertEqual(result.returncode, 0, result.stderr)
                project = ElementTree.parse(consumer / "Bootstrap.Consumer.Contracts.csproj")
                self.assertEqual(project.findtext(".//TargetFramework"), framework)
                self.assert_no_push()

    def test_bootstrap_refuses_compile_framework_different_from_effective_source(self):
        staged = self.staged(framework="net10.0")
        result = self.run_script("validate-release-packages.py", str(staged.parent), "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.endswith("ValueError: Abstractions package is missing its net11.0 compile DLL\n"), result.stderr)
        self.assert_no_push()

    def test_bootstrap_refuses_unsupported_or_multiple_effective_frameworks(self):
        staged = self.staged()
        for framework, frameworks in (("net9.0", ""), ("net11.0", "net10.0;net11.0"), ("", "")):
            with self.subTest(framework=framework, frameworks=frameworks):
                self.env.update(SOURCE_FRAMEWORK=framework, SOURCE_FRAMEWORKS=frameworks)
                result = self.run_script("validate-release-packages.py", str(staged.parent), "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.endswith("ValueError: Bootstrap source must target only net10.0 or net11.0.\n"), result.stderr)
                consumer = self.root / ("refused-consumer-" + str(len(self.calls())))
                result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", str(staged.parent), str(consumer))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.endswith("ValueError: Bootstrap source must target only net10.0 or net11.0.\n"), result.stderr)
                self.assertFalse((consumer / "Bootstrap.Consumer.Contracts.csproj").exists())
                self.assertTrue(all(call[0] == "msbuild" for call in self.calls()))
                self.assert_no_push()

    def test_paired_abstractions_refuses_historical_or_additional_compile_framework(self):
        staged = self.staged(framework="net10.0")
        self.paired_tool()
        result = self.run_script("validate-release-packages.py", str(staged.parent), "1.0.0", "paired", "--source-sha", SHA)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.endswith("ValueError: Abstractions package is missing its net11.0 compile DLL\n"), result.stderr)
        for asset in ("lib/net10.0/Hexalith.McpCli.Abstractions.dll", "ref/net10.0/Hexalith.McpCli.Abstractions.dll",
                      "Ref/net10.0/Hexalith.McpCli.Abstractions.dll"):
            with self.subTest(asset=asset):
                self.staged()
                with ZipFile(staged, "a") as archive:
                    archive.writestr(asset, "historical compile bytes")
                result = self.run_script("validate-release-packages.py", str(staged.parent), "1.0.0", "paired", "--source-sha", SHA)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.endswith("ValueError: Abstractions package must contain only its net11.0 compile target\n"), result.stderr)
                self.assert_no_push()

    def test_paired_abstractions_refuses_rid_specific_payload(self):
        for asset in ("runtimes/linux-x64/lib/net10.0/Hexalith.McpCli.Abstractions.dll",
                      "runtimes/linux-x64/lib/net11.0/Hexalith.McpCli.Abstractions.dll",
                      "runtimes/linux-x64/native/payload.so", "Runtimes/linux-x64/native/payload.so"):
            with self.subTest(asset=asset):
                staged = self.staged()
                self.paired_tool()
                with ZipFile(staged, "a") as archive:
                    archive.writestr(asset, "RID-specific fixture bytes")
                result = self.run_script("validate-release-packages.py", str(staged.parent), "1.0.0", "paired", "--source-sha", SHA)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.endswith("ValueError: Abstractions package cannot contain RID-specific payload\n"), result.stderr)
                self.assert_no_push()

    def test_consumer_uses_fresh_cache_config_and_clears_fallback_folders(self):
        self.env["NUGET_FALLBACK_PACKAGES"] = "/inherited/cache"
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/fixture/empty-source", str(self.root / "consumer"))
        self.assertEqual(result.returncode, 0, result.stderr)
        from xml.etree import ElementTree
        config = ElementTree.fromstring((self.root / "consumer-nuget.config").read_text())
        self.assertIsNotNone(config.find("packageSources/clear"))
        self.assertEqual([node.attrib for node in config.findall("packageSources/add")],
                         [{"key": "verified", "value": "/fixture/empty-source"}])
        self.assertIsNotNone(config.find("fallbackPackageFolders/clear"))
        environment = json.loads((self.root / "consumer-environment.json").read_text())
        self.assertEqual(environment["NUGET_FALLBACK_PACKAGES"], "")
        self.assertEqual(environment["NUGET_PACKAGES"], str(self.root / "consumer/packages"))
        restore, = [call for call in self.calls() if call[0] == "restore"]
        self.assertIn("-p:RestoreFallbackFolders=", restore)
        self.assertIn("-p:RestoreAdditionalProjectFallbackFolders=", restore)
        self.assert_no_push()

    def test_consumer_overrides_inherited_restore_source_and_package_directory(self):
        self.env.update(RestoreSources="/inherited/source", RestorePackagesPath="/inherited/packages")
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", str(self.root / "consumer"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[0] for call in self.calls()], ["msbuild", "restore", "build"])
        for call in self.calls()[1:]:
            self.assertIn("-p:RestoreSources=/selected/source", call)
            self.assertIn(f"-p:RestorePackagesPath={self.root}/consumer/packages", call)
            self.assertIn("-p:RestoreAdditionalProjectSources=", call)
        self.assert_no_push()

    def test_consumer_resolves_relative_sources_from_the_calling_directory(self):
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "relative-source", "consumer")
        self.assertEqual(result.returncode, 0, result.stderr)
        from xml.etree import ElementTree
        config = ElementTree.fromstring((self.root / "consumer-nuget.config").read_text())
        expected = str(self.root / "relative-source")
        self.assertEqual(config.find("packageSources/add").attrib["value"], expected)
        self.assertIn(f"-p:RestoreSources={expected}", self.calls()[1])
        self.assert_no_push()

    def test_consumer_preserves_url_sources_in_config_restore_and_build(self):
        source = "https://api.nuget.org/v3/index.json"
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", source, "consumer")
        self.assertEqual(result.returncode, 0, result.stderr)
        from xml.etree import ElementTree
        config = ElementTree.fromstring((self.root / "consumer-nuget.config").read_text())
        self.assertEqual(config.find("packageSources/add").attrib["value"], source)
        self.assertEqual([call[0] for call in self.calls()], ["msbuild", "restore", "build"])
        for call in self.calls()[1:]:
            self.assertIn(f"-p:RestoreSources={source}", call)
        self.assert_no_push()

    def test_consumer_references_only_abstractions_at_the_exact_requested_version(self):
        from xml.etree import ElementTree
        for version in ("1.0.0", "1.2.3-rc.4"):
            with self.subTest(version=version):
                consumer = self.root / ("consumer-" + version)
                result = self.run_script("smoke-bootstrap-consumer.sh", version, "/selected/source", str(consumer))
                self.assertEqual(result.returncode, 0, result.stderr)
                project = ElementTree.parse(consumer / "Bootstrap.Consumer.Contracts.csproj")
                self.assertEqual([node.attrib for node in project.findall(".//PackageReference")],
                                 [{"Include": "Hexalith.McpCli.Abstractions", "Version": f"[{version}]"}])
                self.assert_no_push()

    def test_consumer_disables_parent_build_and_package_imports(self):
        (self.root / "Directory.Build.props").write_text(
            '<Project><PropertyGroup><TargetFramework>invalid</TargetFramework></PropertyGroup></Project>')
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", str(self.root / "consumer"))
        self.assertEqual(result.returncode, 0, result.stderr)
        for call in self.calls()[1:]:
            for option in ("ImportDirectoryBuildProps", "ImportDirectoryBuildTargets", "ImportDirectoryPackagesProps"):
                self.assertIn(f"-p:{option}=false", call)
        self.assert_no_push()

    def test_consumer_disables_terminal_logger_even_when_forced(self):
        self.env["MSBUILDTERMINALLOGGER"] = "on"
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", "consumer")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[0] for call in self.calls()], ["msbuild", "restore", "build"])
        for call in self.calls():
            self.assertIn("-tl:off", call)
        self.assert_no_push()

    def test_consumer_refuses_reusing_a_directory_before_dotnet(self):
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", "consumer")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", "consumer")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("File exists", result.stderr)
        self.assertEqual(self.calls(), calls)
        self.assert_no_push()


if __name__ == '__main__':
    unittest.main()
