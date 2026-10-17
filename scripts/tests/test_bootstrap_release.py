"""Exercise release entry points with synthetic packages and no external effects."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import warnings
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "Hexalith.McpCli.Abstractions.1.0.0.nupkg"
SHA = "a" * 40


def package(path, *, identity="Hexalith.McpCli.Abstractions", version="1.0.0", missing=(), dependency=False,
            core_properties=None):
    files = {
        "Hexalith.McpCli.Abstractions.nuspec": (
            f'<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"><metadata>'
            f'<id>{identity}</id><version>{version}</version>'
            + ('<dependencies><group><dependency id="Leak" version="1.0.0" /></group></dependencies>' if dependency else '')
            + '</metadata></package>'
        ),
        "lib/net10.0/Hexalith.McpCli.Abstractions.dll": "compile fixture",
        "analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll": "analyzer fixture",
    }
    if core_properties is not None:
        files["package/services/metadata/core-properties/nuget.psmdcp"] = core_properties
    with ZipFile(path, "w") as archive:
        for name, contents in files.items():
            if name not in missing:
                archive.writestr(name, contents)


class BootstrapReleaseTests(unittest.TestCase):
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
        self.env = dict(os.environ, MCPCLI_RELEASE_PHASE="bootstrap", NUGET_API_KEY="fixture-secret-never-print",
                        PATH=f"{self.bin}:{os.environ['PATH']}", PYTHONPATH=str(self.bin),
                        RELEASE_TEST_ROOT=str(self.root), REGISTRY_STATE="404", SOURCE_STATE="success",
                        REPOSITORY="fixture/repo", DISPATCH_SHA=SHA, DISPATCH_REF="refs/heads/main")
        (self.bin / "sitecustomize.py").write_text('''
import io, json, os
from pathlib import Path
from urllib.error import HTTPError
import urllib.request
def registry(url, timeout):
    root = Path(os.environ["RELEASE_TEST_ROOT"])
    with (root / "registry.log").open("a") as log: log.write(url + "\\n")
    state = os.environ["REGISTRY_STATE"]
    if url.endswith(".nupkg"):
        if os.environ.get("PUBLIC_STATE") == "timeout": raise TimeoutError("fixture")
        body = (root / "public.nupkg").read_bytes()
        response = io.BytesIO(body)
        response.status = 200
        return response
    if state in ("404", "403", "500"):
        raise HTTPError(url, int(state), "fixture", {}, None)
    if state == "timeout": raise TimeoutError("fixture")
    body = {"free": '{"versions":["0.9.0"]}', "taken": '{"versions":["1.0.0"]}',
            "case-taken": '{"versions":["1.0.0-RC.1"]}', "bad-json": '{',
            "bad-shape": '{"versions":[1]}', "empty": '{"versions":[]}',
            "blank-version": '{"versions":[""]}', "whitespace-version": '{"versions":[" "]}',
            "nonsense-version": '{"versions":["not-a-version"]}',
            "partial-version": '{"versions":["1.0"]}'}.get(state, '{}')
    response = io.BytesIO(body.encode())
    response.status = 201 if state == "unexpected-status" else 200
    return response
urllib.request.urlopen = registry
''')
        self.executable("dotnet", '''#!/usr/bin/env python3
import hashlib, json, os, sys
from pathlib import Path
from zipfile import ZipFile
root = Path(os.environ["RELEASE_TEST_ROOT"])
args = sys.argv[1:]
safe = ["REDACTED" if i and args[i-1] == "--api-key" else arg for i, arg in enumerate(args)]
with (root / "dotnet.log").open("a") as log: log.write(json.dumps(safe) + "\\n")
if args[0] == "pack":
    if os.environ.get("PACK_FAIL"): sys.exit(1)
    directory = Path(args[args.index("--output") + 1])
    version = next(arg.split("=", 1)[1] for arg in args if arg.startswith("-p:Version="))
    with ZipFile(directory / f"Hexalith.McpCli.Abstractions.{version}.nupkg", "w") as archive:
        archive.writestr("Abstractions.nuspec", f"<package><metadata><id>Hexalith.McpCli.Abstractions</id><version>{version}</version></metadata></package>")
        archive.writestr("lib/net10.0/Hexalith.McpCli.Abstractions.dll", "compile fixture")
        archive.writestr("analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll", "analyzer fixture")
    if os.environ.get("AFTER_PACK_SOURCE_STATE"):
        (root / "local-source-state").write_text(os.environ["AFTER_PACK_SOURCE_STATE"])
if "Bootstrap.Consumer.Contracts.csproj" in args[1]:
    (root / "consumer-environment.json").write_text(json.dumps({name: os.environ.get(name) for name in
        ("NUGET_PACKAGES", "NUGET_FALLBACK_PACKAGES", "NUGET_HTTP_CACHE_PATH")}))
    if os.environ.get("SMOKE_FAIL"): sys.exit(1)
    if args[0] == "restore":
        (root / "consumer-nuget.config").write_text(Path(args[args.index("--configfile") + 1]).read_text())
    if args[0] == "build": print("warning MCPCLI001: fixture\\n    1 Warning(s)")
if args[:2] == ["nuget", "push"]:
    package = Path(args[2])
    (root / "pushed.sha256").write_text(hashlib.sha256(package.read_bytes()).hexdigest())
    (root / "pushed.path").write_text(str(package))
''')
        self.executable("git", '''#!/usr/bin/env python3
import os, sys
from pathlib import Path
state = os.environ.get("LOCAL_SOURCE_STATE", "clean")
state_file = Path(os.environ["RELEASE_TEST_ROOT"]) / "local-source-state"
if state_file.exists(): state = state_file.read_text()
if state == "not-git": sys.exit(128)
if sys.argv[1:] == ["rev-parse", "HEAD"]: print("b" * 40 if state == "wrong-head" else os.environ.get("LOCAL_HEAD_SHA", "a" * 40))
elif sys.argv[1:] == ["rev-parse", "--verify", "refs/tags/v1.0.0^{commit}"]:
    print(os.environ.get("TAG_SHA", "a" * 40))
elif sys.argv[1:] == ["rev-parse", "origin/main"]:
    print(os.environ.get("FETCHED_MAIN_SHA", os.environ.get("LIVE_SHA", "a" * 40)))
elif sys.argv[1:3] == ["merge-base", "--is-ancestor"]:
    if os.environ.get("RECOVERY_ANCESTOR") == "false": sys.exit(1)
elif sys.argv[1:] == ["branch", "--show-current"]: print("feature" if state == "feature" else "main")
elif sys.argv[1:] == ["status", "--porcelain", "--untracked-files=normal"]:
    if state == "dirty": print(" M scripts/release-publish.sh")
    if state == "untracked": print("?? scripts/unreviewed.py")
else: sys.exit(1)
''')
        self.executable("gh", '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
state = os.environ["SOURCE_STATE"]
sha = os.environ.get("LIVE_SHA", "a" * 40)
run_sha = os.environ.get("RUN_SHA", "a" * 40)
with (Path(os.environ["RELEASE_TEST_ROOT"]) / "gh.log").open("a") as log: log.write(" ".join(sys.argv[1:]) + "\\n")
endpoint = sys.argv[4]
if endpoint.endswith("git/ref/heads/main"):
    print(json.dumps({"object":{"sha":"b" * 40 if state == "stale" else sha}}))
elif endpoint.endswith("git/ref/tags/v1.0.0"):
    if os.environ.get("REMOTE_TAG_ANNOTATED") == "1":
        print(json.dumps({"object":{"type":"tag", "sha":"t" * 40}}))
    else:
        print(json.dumps({"object":{"type":"commit", "sha":os.environ.get("REMOTE_TAG_SHA", "a" * 40)}}))
elif endpoint.endswith("git/tags/" + "t" * 40):
    print(json.dumps({"object":{"type":"commit", "sha":os.environ.get("REMOTE_TAG_SHA", "a" * 40)}}))
else:
    gate = "bootstrap" if "bootstrap-package" in endpoint else "commitlint"
    run = {"head_sha":run_sha, "head_branch":"main", "event":"push", "status":"completed",
           "conclusion":"success", "run_number":1, "run_attempt":1, "html_url":"https://example.test/" + gate}
    runs = [run]
    if state == gate + "-missing": runs = []
    elif state == gate + "-failed": run["conclusion"] = "failure"
    elif state == gate + "-pending": run["status"] = "in_progress"; run["conclusion"] = None
    elif state == gate + "-other-sha": run["head_sha"] = "c" * 40
    elif state == gate + "-pull-request": run["event"] = "pull_request"
    elif state == gate + "-rerun-failed": runs.append(dict(run, run_attempt=2, conclusion="failure"))
    elif state == gate + "-new-run-failed":
        runs = [dict(run, run_attempt=9), dict(run, run_number=2, conclusion="failure")]
    elif state == gate + "-new-run-success":
        runs = [dict(run, run_attempt=9, conclusion="failure"), dict(run, run_number=2)]
    elif state == gate + "-rerun-success":
        runs = [dict(run, run_attempt=2), dict(run, conclusion="failure")]
    print(json.dumps({"workflow_runs":runs}))
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

    def test_prepare_builds_only_bootstrap_and_preserves_other_artifacts(self):
        other = self.root / "nupkgs/unrelated.nupkg"
        other.parent.mkdir()
        other.write_bytes(b"preserve me")
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual([call[0] for call in calls], ["restore", "build", "pack", "restore", "build"])
        for call in calls[:3]:
            self.assertEqual(call[1], "src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj")
        self.assertEqual(other.read_bytes(), b"preserve me")
        self.assertFalse((self.root / "registry.log").exists())
        self.assert_no_push()
        prepared = (self.root / "nupkgs/bootstrap" / PACKAGE).read_bytes()
        retry = self.run_script("release-prepare.sh", "1.0.0")
        self.assertNotEqual(retry.returncode, 0)
        self.assertIn("already exists", retry.stderr)
        self.assertEqual((self.root / "nupkgs/bootstrap" / PACKAGE).read_bytes(), prepared)
        self.assertEqual(len(self.calls()), 5)

    def test_failed_prepare_cleans_only_its_own_staging(self):
        self.env["PACK_FAIL"] = "1"
        other = self.root / "nupkgs/other.txt"
        other.parent.mkdir()
        other.write_text("keep")
        self.assertNotEqual(self.run_script("release-prepare.sh", "1.0.0").returncode, 0)
        self.assertEqual(other.read_text(), "keep")
        self.assertFalse((other.parent / "bootstrap").exists())
        self.assert_no_push()

    def test_prepare_to_publish_uses_the_generated_source_bound_receipt(self):
        result = self.run_script("release-prepare.sh", "1.0.0", "--verify-source")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.root / "nupkgs/bootstrap" / PACKAGE
        expected_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        receipt = json.loads((self.root / "nupkgs/bootstrap.sha256").read_text())
        self.assertEqual(receipt, {"sha256": expected_hash, "source_sha": SHA, "source_clean": True})
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "pushed.sha256").read_text(), expected_hash)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 1)

    def test_dirty_preparation_cannot_publish_or_recover_after_source_is_cleaned(self):
        self.env["LOCAL_SOURCE_STATE"] = "dirty"
        self.env["AFTER_PACK_SOURCE_STATE"] = "clean"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.root / "nupkgs/bootstrap.sha256").read_text())
        self.assertIs(receipt["source_clean"], False)
        for script, args in (("release-publish.sh", ("1.0.0",)),
                             ("recover-bootstrap-release.py", ("1.0.0", "bootstrap"))):
            with self.subTest(script=script):
                result = self.run_script(script, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("receipt records dirty source", result.stderr)
                self.assert_no_push()

    def test_older_preparation_cannot_publish_or_recover_from_new_green_source(self):
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.env.update(LOCAL_HEAD_SHA="b" * 40, LIVE_SHA="b" * 40, DISPATCH_SHA="b" * 40,
                        TAG_SHA="b" * 40, REMOTE_TAG_SHA="b" * 40, RUN_SHA="b" * 40)
        for script, args in (("release-publish.sh", ("1.0.0",)),
                             ("recover-bootstrap-release.py", ("1.0.0", "bootstrap"))):
            with self.subTest(script=script):
                result = self.run_script(script, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("receipt source SHA does not match", result.stderr)
                self.assert_no_push()

    def test_preparation_refuses_a_head_change_during_the_build(self):
        self.env["AFTER_PACK_SOURCE_STATE"] = "wrong-head"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source HEAD changed", result.stderr)
        self.assertFalse((self.root / "nupkgs/bootstrap.sha256").exists())
        self.assert_no_push()

    def test_invalid_requests_are_rejected_by_every_entry_point_before_effects(self):
        for script in ("release-prepare.sh", "release-preflight.sh", "release-publish.sh"):
            for phase, version, message in (("paired", "1.0.0", "deferred"), ("unknown", "1.0.0", "Unknown"),
                    *(("bootstrap", version, "Invalid") for version in (
                        "1.0", "01.0.0", "1.0.0-", "1.0.0-01", "1.0.0-a..b", "1.0.0+meta", "1.0.0\n",
                        "2147483648.0.0", "0.2147483648.0", "0.0.2147483648"))):
                with self.subTest(script=script, phase=phase, version=version):
                    self.env["MCPCLI_RELEASE_PHASE"] = phase
                    result = self.run_script(script, version)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertEqual(self.calls(), [])
                    self.assert_no_push()
                    self.assertFalse((self.root / "registry.log").exists())
                    self.assertFalse((self.root / "nupkgs").exists())

    def test_missing_credentials_rejected_by_preflight_and_direct_publish(self):
        for script in ("release-preflight.sh", "release-publish.sh"):
            with self.subTest(script=script):
                self.env["NUGET_API_KEY"] = " "
                result = self.run_script(script, "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("publication key is required", result.stderr)
                self.assertFalse((self.root / "registry.log").exists())
                self.assert_no_push()

    def test_registry_rejections_prevent_direct_publication(self):
        self.staged()
        for state in ("taken", "403", "500", "timeout", "bad-json", "bad-shape", "empty", "unexpected-status",
                      "blank-version", "whitespace-version", "nonsense-version", "partial-version"):
            with self.subTest(state=state):
                self.env["REGISTRY_STATE"] = state
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("already published" if state == "taken" else "Could not confirm", result.stderr)
                self.assert_no_push()

    def test_case_insensitive_registry_identity(self):
        self.env["REGISTRY_STATE"] = "case-taken"
        result = self.run_script("release-preflight.sh", "1.0.0-rc.1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already published", result.stderr)
        self.assert_no_push()

    def test_invalid_package_matrix_never_pushes(self):
        cases = (
            ({"identity": "Wrong"}, "Unexpected package ID"),
            ({"version": "2.0.0"}, "Unexpected package version"),
            ({"missing": ("lib/net10.0/Hexalith.McpCli.Abstractions.dll",)}, "compile DLL"),
            ({"missing": ("analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll",)}, "analyzer DLL"),
            ({"dependency": True}, "consumer-visible package dependencies"),
            ({"missing": ("Hexalith.McpCli.Abstractions.nuspec",)}, "one nuspec"),
        )
        for options, message in cases:
            with self.subTest(options=options):
                self.staged(**options)
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()

    def test_extra_artifacts_and_symbol_packages_are_rejected(self):
        path = self.staged()
        for name in ("Unexpected.1.0.0.nupkg", "symbols.snupkg", "extra.txt", "subdirectory"):
            with self.subTest(name=name):
                extra = path.parent / name
                extra.write_text("unexpected")
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Expected", result.stderr)
                self.assert_no_push()
                extra.unlink()

    def test_duplicate_archive_entries_and_symlink_packages_are_rejected(self):
        path = self.staged()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(path, "a") as archive:
                archive.writestr("lib/net10.0/Hexalith.McpCli.Abstractions.dll", "duplicate")
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate archive entries", result.stderr)
        path.unlink()
        outside = self.root / "outside.nupkg"
        package(outside)
        path.symlink_to(outside)
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular package file", result.stderr)
        self.assert_no_push()

    def test_modified_prepared_package_is_rejected(self):
        path = self.staged()
        with ZipFile(path, "a") as archive:
            archive.writestr("README.md", "changed after preparation")
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed after preparation", result.stderr)
        self.assert_no_push()

    def test_missing_or_invalid_receipt_is_rejected(self):
        self.staged()
        receipt = self.root / "nupkgs/bootstrap.sha256"
        for contents in (None, "invalid", "a" * 64):
            with self.subTest(contents=contents):
                if contents is None:
                    receipt.unlink()
                else:
                    receipt.write_text(contents)
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("receipt", result.stderr)
                self.assert_no_push()

    def test_missing_package_and_malformed_archives_are_rejected(self):
        path = self.staged()
        path.unlink()
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected", result.stderr)
        path.write_text("not a zip")
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a zip", result.stderr)
        self.staged()
        with ZipFile(path, "a") as archive:
            archive.writestr("other.nuspec", "<package />")
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("one nuspec", result.stderr)
        self.assert_no_push()

    def paired_tool(self, *, missing=(), package_type=True, command=None, manifest='("Sample.Contracts", "Sample.Contracts")', assembly=True):
        prefix = "tools/net10.0/any/"
        files = {
            "Hexalith.McpCli.nuspec": '<package><metadata><id>Hexalith.McpCli</id><version>1.0.0</version>'
                + ('<packageTypes><packageType name="DotnetTool" /></packageTypes>' if package_type else '')
                + '</metadata></package>',
            "README.md": "fixture", prefix + "Hexalith.McpCli.dll": "fixture",
            prefix + "Hexalith.McpCli.deps.json": "{}", prefix + "Hexalith.McpCli.runtimeconfig.json": "{}",
            prefix + "DotnetToolSettings.xml": '<DotNetCliTool><Commands><Command '
                + (command if command is not None else 'Name="hexalith" EntryPoint="Hexalith.McpCli.dll" Runner="dotnet"')
                + ' /></Commands></DotNetCliTool>',
        }
        if assembly:
            files[prefix + "Sample.Contracts.dll"] = "fixture"
        with ZipFile(self.root / "nupkgs/bootstrap/Hexalith.McpCli.1.0.0.nupkg", "w") as archive:
            for name, contents in files.items():
                if name not in missing:
                    archive.writestr(name, contents)
        path = self.root / "src/Hexalith.McpCli/obj/Release/net10.0/ModuleAssemblyManifest.g.cs"
        path.parent.mkdir(parents=True, exist_ok=True)
        if manifest is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(manifest)

    def test_paired_validation_keeps_existing_tool_structure_checks(self):
        path = self.staged()
        prefix = "tools/net10.0/any/"
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
                result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "paired")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()
        self.paired_tool()
        result = self.run_script("validate-release-packages.py", str(path.parent), "1.0.0", "paired")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_no_push()

    def test_staging_directory_and_receipt_symlinks_are_rejected(self):
        path = self.staged()
        actual = self.root / "preserved-staging"
        path.parent.rename(actual)
        path.parent.symlink_to(actual, target_is_directory=True)
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Staging must be a real directory", result.stderr)
        self.assert_no_push()
        path.parent.unlink()
        actual.rename(path.parent)
        receipt = path.parent.parent / "bootstrap.sha256"
        outside = self.root / "preserved-receipt"
        receipt.rename(outside)
        receipt.symlink_to(outside)
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt is missing or invalid", result.stderr)
        self.assert_no_push()

    def test_prepare_refuses_existing_staging_and_receipt_symlinks(self):
        (self.root / "nupkgs").mkdir()
        for name in ("bootstrap", "bootstrap.sha256"):
            with self.subTest(name=name):
                guard = self.root / "nupkgs" / name
                guard.symlink_to(self.root / "missing-target")
                result = self.run_script("release-prepare.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("already exists", result.stderr)
                self.assertTrue(guard.is_symlink())
                self.assertEqual(self.calls(), [])
                self.assert_no_push()
                guard.unlink()

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
        restore = self.calls()[0]
        self.assertIn("-p:RestoreFallbackFolders=", restore)
        self.assertIn("-p:RestoreAdditionalProjectFallbackFolders=", restore)
        self.assert_no_push()

    def test_consumer_overrides_inherited_restore_source_and_package_directory(self):
        self.env.update(RestoreSources="/inherited/source", RestorePackagesPath="/inherited/packages")
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", str(self.root / "consumer"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[0] for call in self.calls()], ["restore", "build"])
        for call in self.calls():
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
        self.assertIn(f"-p:RestoreSources={expected}", self.calls()[0])
        self.assert_no_push()

    def test_consumer_disables_parent_build_and_package_imports(self):
        (self.root / "Directory.Build.props").write_text(
            '<Project><PropertyGroup><TargetFramework>invalid</TargetFramework></PropertyGroup></Project>')
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", str(self.root / "consumer"))
        self.assertEqual(result.returncode, 0, result.stderr)
        for call in self.calls():
            for option in ("ImportDirectoryBuildProps", "ImportDirectoryBuildTargets", "ImportDirectoryPackagesProps"):
                self.assertIn(f"-p:{option}=false", call)
        self.assert_no_push()

    def test_failed_consumer_smoke_prevents_preparation_receipt(self):
        self.env["SMOKE_FAIL"] = "1"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "nupkgs/bootstrap.sha256").exists())
        self.assertFalse((self.root / "nupkgs/bootstrap").exists())
        self.assert_no_push()

    def test_source_is_rechecked_after_preparation_before_tagging(self):
        self.env["SOURCE_STATE"] = "stale"
        result = self.run_script("release-prepare.sh", "1.0.0", "--verify-source")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call[0] for call in self.calls()], ["restore", "build", "pack", "restore", "build"])
        self.assertFalse((self.root / "nupkgs/bootstrap.sha256").exists())
        self.assert_no_push()

    def test_direct_publish_requires_exact_committed_source_and_independent_gates(self):
        self.staged()
        for state in ("not-git", "wrong-head", "feature", "dirty", "untracked"):
            with self.subTest(state=state):
                self.env["LOCAL_SOURCE_STATE"] = state
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("source gate failed", result.stderr)
                self.assert_no_push()
        self.env["LOCAL_SOURCE_STATE"] = "clean"
        for state in ("stale", "bootstrap-failed", "commitlint-missing"):
            with self.subTest(state=state):
                self.env["SOURCE_STATE"] = state
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("source gate failed", result.stderr)
                self.assert_no_push()

    def test_recovery_publishes_absent_package_then_verifies_public_content(self):
        staged = self.staged()
        shutil.copy(staged, self.root / "public.nupkg")
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified public package", result.stdout)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 1)

    def test_tagged_recovery_uses_preserved_scripts_and_green_ancestor_after_main_moves(self):
        staged = self.staged()
        shutil.copy(staged, self.root / "public.nupkg")
        self.env["LIVE_SHA"] = "b" * 40
        self.env["REMOTE_TAG_ANNOTATED"] = "1"
        preserved = self.root / "runner-temp/release-scripts"
        shutil.copytree(self.root / "scripts", preserved)
        (self.root / "scripts/release-publish.sh").write_text(
            '#!/usr/bin/env bash\necho "tagged publisher cannot check moved main" >&2\nexit 91\n')
        (self.root / "scripts/verify-release-source.py").write_text(
            'import sys\nprint("tagged source verifier cannot check moved main", file=sys.stderr)\nsys.exit(91)\n')
        result = subprocess.run(["python3", str(preserved / "recover-bootstrap-release.py"), "1.0.0", "bootstrap"],
                                cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified tagged recovery source", result.stdout)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 1)

    def test_tagged_recovery_rejects_wrong_tag_moved_main_nonancestor_and_failed_gate(self):
        self.staged()
        self.env["LIVE_SHA"] = "b" * 40
        for changed, value, message in (("TAG_SHA", "c" * 40, "Recovery tag does not match"),
                                        ("REMOTE_TAG_SHA", "c" * 40, "Remote recovery tag does not match"),
                                        ("FETCHED_MAIN_SHA", "c" * 40, "Current main moved"),
                                        ("RECOVERY_ANCESTOR", "false", "not an ancestor"),
                                        ("SOURCE_STATE", "bootstrap-failed", "No successful latest")):
            with self.subTest(changed=changed):
                self.env[changed] = value
                result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()
                del self.env[changed]

    def test_recovery_publisher_refuses_version_mismatch(self):
        self.staged()
        self.env["MCPCLI_RECOVERY_VERSION"] = "1.0.1"
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Recovery version does not match", result.stderr)
        self.assert_no_push()

    def test_recovery_absent_publisher_uses_validated_phase_over_ambient_phase(self):
        staged = self.staged()
        shutil.copy(staged, self.root / "public.nupkg")
        for ambient in (None, "paired", "unknown"):
            with self.subTest(ambient=ambient):
                if ambient is None:
                    self.env.pop("MCPCLI_RELEASE_PHASE", None)
                else:
                    self.env["MCPCLI_RELEASE_PHASE"] = ambient
                result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 3)

    def test_recovery_verifies_matching_existing_package_without_republishing(self):
        staged = self.staged(core_properties="original generated build metadata")
        with ZipFile(staged) as prepared, ZipFile(self.root / "public.nupkg", "w") as archive:
            for name in prepared.namelist():
                contents = (b"different registry core properties" if name.endswith(".psmdcp") else prepared.read(name))
                archive.writestr(name, contents)
            archive.writestr(".signature.p7s", "registry signature fixture")
        self.env["REGISTRY_STATE"] = "taken"
        self.env["NUGET_API_KEY"] = ""
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("without a second push", result.stdout)
        self.assertIn("Verified public package", result.stdout)
        self.assert_no_push()

    def test_recovery_rejects_mismatching_public_package_without_push(self):
        self.staged()
        package(self.root / "public.nupkg", dependency=True)
        self.env["REGISTRY_STATE"] = "taken"
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("consumer-visible package dependencies", result.stderr)
        package(self.root / "public.nupkg")
        with ZipFile(self.root / "public.nupkg", "a") as archive:
            archive.writestr("README.md", "unexpected content")
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content does not match", result.stderr)
        self.assert_no_push()

    def test_recovery_rejects_uncertain_registry_and_download_states_without_push(self):
        staged = self.staged()
        shutil.copy(staged, self.root / "public.nupkg")
        for state in ("timeout", "500", "bad-json", "nonsense-version"):
            with self.subTest(state=state):
                self.env["REGISTRY_STATE"] = state
                result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Could not confirm", result.stderr)
                self.assert_no_push()
        self.env["REGISTRY_STATE"] = "taken"
        self.env["PUBLIC_STATE"] = "timeout"
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Could not verify the public package", result.stderr)
        self.assert_no_push()

    def test_publication_pushes_one_validated_snapshot_with_exact_prepared_hash(self):
        path = self.staged()
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        for state in ("404", "free"):
            with self.subTest(state=state):
                self.env["REGISTRY_STATE"] = state
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((self.root / "pushed.sha256").read_text(), expected)
                pushed = Path((self.root / "pushed.path").read_text())
                self.assertNotEqual(pushed.parent, path.parent)
                self.assertFalse(pushed.exists())  # Private snapshot is cleaned after push.
        self.assertEqual(len(self.calls()), 2)
        for call in self.calls():
            self.assertEqual(call[:2], ["nuget", "push"])
            self.assertEqual(Path(call[2]).name, PACKAGE)
            self.assertNotIn("--skip-duplicate", call)

    def test_source_rejections_require_current_main_and_both_latest_results(self):
        result = self.run_script("verify-release-source.py", SHA, "refs/heads/feature", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refs/heads/main", result.stderr)
        self.assertFalse((self.root / "gh.log").exists())
        for sha, phase, message in (("invalid", "bootstrap", "exact source SHA"),
                                     (SHA, "paired", "paired release remains deferred")):
            with self.subTest(sha=sha, phase=phase):
                result = self.run_script("verify-release-source.py", sha, "refs/heads/main", phase)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse((self.root / "gh.log").exists())
        for state in ("stale", *(f"{gate}-{failure}" for gate in ("bootstrap", "commitlint") for failure in
                                ("missing", "failed", "pending", "other-sha", "pull-request", "rerun-failed"))):
            with self.subTest(state=state):
                self.env["SOURCE_STATE"] = state
                result = self.run_script("verify-release-source.py", SHA, "refs/heads/main", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("source gate failed", result.stderr)
                self.assert_no_push()

    def test_source_gate_requires_no_full_tool_ci_or_module_prerequisite(self):
        result = self.run_script("verify-release-source.py", SHA, "refs/heads/main", "bootstrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.root / "gh.log").read_text()
        self.assertIn("bootstrap-package.yml", calls)
        self.assertIn("commitlint.yml", calls)
        self.assertNotIn("/ci.yml", calls)
        self.assert_no_push()

    def test_source_gate_orders_run_number_before_attempt_and_latest_attempt_within_run(self):
        for gate in ("bootstrap", "commitlint"):
            for state, succeeds in (("new-run-failed", False), ("new-run-success", True),
                                    ("rerun-failed", False), ("rerun-success", True)):
                with self.subTest(gate=gate, state=state):
                    self.env["SOURCE_STATE"] = f"{gate}-{state}"
                    result = self.run_script("verify-release-source.py", SHA, "refs/heads/main", "bootstrap")
                    self.assertEqual(result.returncode == 0, succeeds, result.stderr)
                    self.assert_no_push()


if __name__ == "__main__":
    unittest.main()
