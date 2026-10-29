"""Exercise release entry points with synthetic packages and no external effects."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
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
        # LC_ALL=C keeps system messages such as mkdir's "File exists" untranslated.
        self.env = dict(os.environ, MCPCLI_RELEASE_PHASE="bootstrap", NUGET_API_KEY="fixture-secret-never-print",
                        LC_ALL="C", PATH=f"{self.bin}:{os.environ['PATH']}", PYTHONPATH=str(self.bin),
                        RELEASE_TEST_ROOT=str(self.root), REGISTRY_STATE="free", SOURCE_STATE="success",
                        REPOSITORY="fixture/repo", DISPATCH_SHA=SHA, DISPATCH_REF="refs/heads/main")
        self.workflow_exports = {}
        (self.bin / "sitecustomize.py").write_text('''
import io, json, os, time
from pathlib import Path
from urllib.error import HTTPError, URLError
import urllib.request
def registry(url, timeout):
    root = Path(os.environ["RELEASE_TEST_ROOT"])
    with (root / "registry.log").open("a") as log: log.write(url + "\\n")
    state = os.environ["REGISTRY_STATE"]
    if url.endswith(".nupkg"):
        public_state = os.environ.get("PUBLIC_STATE")
        downloads = root / "downloads.log"
        previous_downloads = len(downloads.read_text().splitlines()) if downloads.exists() else 0
        with downloads.open("a") as log: log.write(url + "\\n")
        if public_state == "timeout": raise TimeoutError("fixture")
        if public_state == "url-error": raise URLError(os.environ["NUGET_API_KEY"])
        if public_state in ("404", "500") or (public_state == "404-then-200" and previous_downloads == 0):
            raise HTTPError(url, 404 if public_state == "404-then-200" else int(public_state), "fixture", {}, None)
        body = (root / "public.nupkg").read_bytes()
        response = io.BytesIO(body)
        response.status = 201 if public_state == "unexpected-status" else 200
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
def sleep(seconds):
    with (Path(os.environ["RELEASE_TEST_ROOT"]) / "sleeps.log").open("a") as log: log.write(str(seconds) + "\\n")
time.sleep = sleep
if os.environ.get("PUBLIC_WRITE_FAIL"):
    original_write_bytes = Path.write_bytes
    def write_bytes(path, data):
        if path.parent.name == "public" and path.suffix == ".nupkg":
            raise OSError("fixture: No space left on device")
        return original_write_bytes(path, data)
    Path.write_bytes = write_bytes
''')
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
    print(json.dumps({"Properties": {"TargetFramework": "net10.0", "TargetFrameworks": "", "PackAsTool": "true", "ToolCommandName": "hexalith", "UseAppHost": "false", "PublishTrimmed": "false", "PublishAot": "false", "PublishReadyToRun": "false", "SelfContained": "false", "RuntimeIdentifier": "", "RuntimeIdentifiers": "", "CreateRidSpecificToolPackages": "false", "PackageId": Path(project).stem, "Version": "1.0.0"}}))
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
        archive.writestr("lib/net10.0/Hexalith.McpCli.Abstractions.dll", "compile fixture")
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
        self.executable("git", '''#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ["RELEASE_TEST_ROOT"])
state = os.environ.get("LOCAL_SOURCE_STATE", "clean")
state_file = root / "local-source-state"
if state_file.exists(): state = state_file.read_text()
if state == "not-git":
    print(os.environ.get("SUBPROCESS_STDERR", "") + chr(0), file=sys.stderr)
    sys.exit(128)
if sys.argv[1:] == ["rev-parse", "HEAD"]:
    checkout = root / "checkout-sha"
    print(checkout.read_text() if checkout.exists() else "b" * 40 if state == "wrong-head" else os.environ.get("LOCAL_HEAD_SHA", "a" * 40))
elif sys.argv[1:] in (["rev-parse", "--verify", "refs/tags/v1.0.0^{commit}"],
                      ["rev-parse", "-q", "--verify", "refs/tags/v1.0.0^{commit}"]):
    if os.environ.get("TAG_EXISTS") == "false": sys.exit(1)
    print(os.environ.get("TAG_SHA", "a" * 40))
elif sys.argv[1:] == ["checkout", "--detach", "v1.0.0"]:
    (root / "checkout-sha").write_text(os.environ.get("TAG_SHA", "a" * 40))
    state_file.write_text("detached")
    if os.environ.get("SABOTAGE_TAGGED_SCRIPTS"):
        for script in (root / "scripts").iterdir():
            if script.suffix == ".sh":
                script.write_text('#!/usr/bin/env bash\\necho "tagged helper called" >> "$RELEASE_TEST_ROOT/tagged-helper.log"\\nexit 91\\n')
            elif script.suffix == ".py":
                script.write_text('from pathlib import Path\\nimport os\\nPath(os.environ["RELEASE_TEST_ROOT"]).joinpath("tagged-helper.log").write_text("called")\\nraise RuntimeError("tagged helper must not run")\\n')
elif sys.argv[1:] == ["rev-parse", "origin/main"]:
    print(os.environ.get("FETCHED_MAIN_SHA", os.environ.get("LIVE_SHA", "a" * 40)))
elif sys.argv[1:3] == ["merge-base", "--is-ancestor"]:
    if sys.argv[3:] not in ([os.environ.get("TAG_SHA", "a" * 40), "origin/main"], ["v1.0.0", "origin/main"]): sys.exit(1)
    if os.environ.get("RECOVERY_ANCESTOR") == "false": sys.exit(1)
elif sys.argv[1:] == ["branch", "--show-current"]: print("" if state == "detached" else "feature" if state == "feature" else "main")
elif sys.argv[1:] == ["status", "--porcelain", "--untracked-files=normal"]:
    if state == "dirty": print(" M scripts/release-publish.sh")
    if state == "untracked": print("?? scripts/unreviewed.py")
else: sys.exit(1)
''')
        self.executable("gh", '''#!/usr/bin/env python3
import json, os, shutil, sys
from pathlib import Path
root = Path(os.environ["RELEASE_TEST_ROOT"])
args = sys.argv[1:]
if args[0] == "release":
    operation = args[1]
    with (root / "github-release.log").open("a") as log: log.write(json.dumps(args) + "\\n")
    if os.environ.get("GITHUB_RELEASE_FAIL") == operation:
        print("fixture release " + operation + " failed", file=sys.stderr)
        sys.exit(42)
    state_path = root / "github-release.json"
    release = json.loads(state_path.read_text()) if state_path.exists() else None
    if operation == "view":
        if release is None: sys.exit(1)
        if args[3:] != ["--json", "isDraft", "--jq", ".isDraft"]: sys.exit(2)
        print("true" if release["isDraft"] else "false")
    elif operation in ("upload", "create"):
        if (release is None) != (operation == "create"): sys.exit(3)
        assets = [Path(argument) for argument in args[3:] if argument.endswith(".nupkg")]
        if not assets or not all(asset.is_file() for asset in assets): sys.exit(4)
        release = release or {"isDraft": False, "assets": []}
        existing = set(release["assets"])
        if operation == "upload" and "--clobber" not in args and any(asset.name in existing for asset in assets):
            print("fixture release asset already exists; use --clobber", file=sys.stderr)
            sys.exit(7)
        destination = root / "github-assets"
        destination.mkdir(exist_ok=True)
        for asset in assets: shutil.copyfile(asset, destination / asset.name)
        release["assets"] = sorted(existing | {asset.name for asset in assets})
        state_path.write_text(json.dumps(release))
    elif operation == "edit":
        if release is None or args[3:] != ["--draft=false"]: sys.exit(5)
        release["isDraft"] = False
        state_path.write_text(json.dumps(release))
    else: sys.exit(6)
    sys.exit(0)
state = os.environ["SOURCE_STATE"]
sha = os.environ.get("LIVE_SHA", "a" * 40)
run_sha = os.environ.get("RUN_SHA", "a" * 40)
with (Path(os.environ["RELEASE_TEST_ROOT"]) / "gh.log").open("a") as log: log.write(" ".join(sys.argv[1:]) + "\\n")
if state == "permission-denied":
    print(os.environ["SUBPROCESS_STDERR"] + chr(0), file=sys.stderr)
    sys.exit(1)
endpoint = sys.argv[4]
if endpoint.endswith("git/ref/heads/main"):
    print(json.dumps({"object":{"sha":"b" * 40 if state == "stale" else sha}}))
elif endpoint.endswith("git/ref/tags/v1.0.0"):
    if os.environ.get("REMOTE_TAG_ANNOTATED") == "1":
        print(json.dumps({"object":{"type":"tag", "sha":"t" * 40}}))
    else:
        print(json.dumps({"object":{"type":os.environ.get("REMOTE_TAG_TYPE", "commit"), "sha":os.environ.get("REMOTE_TAG_SHA", "a" * 40)}}))
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
    elif state == gate + "-other-branch": run["head_branch"] = "feature"
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

    def complete_github_release(self):
        preserved = self.root / "runner-temp/release-scripts"
        preserved.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.root / "scripts/verify-release-source.py", preserved / "verify-release-source.py")
        self.env.update(RUNNER_TEMP=str(preserved.parent), RECOVERY_VERSION="1.0.0")
        self.workflow_exports["DISPATCH_SHA"] = SHA
        return self.run_workflow_step("recover", "Complete the GitHub release")

    def workflow_step(self, job, name):
        workflow = (ROOT / ".github/workflows/release.yml").read_text()
        job_block = re.split(r"(?m)^  [\w-]+:\n", workflow.split(f"  {job}:\n", 1)[1], maxsplit=1)[0]
        return job_block.split(f"      - name: {name}\n", 1)[1].split("\n      - ", 1)[0]

    def run_workflow_step(self, job, name):
        block = self.workflow_step(job, name)
        environment = dict(self.env)
        for key in ("DISPATCH_SHA", "DISPATCH_REF", "REPOSITORY", "MCPCLI_RELEASE_PHASE", "RECOVERY_VERSION",
                    "RECOVERY_PHASE", "GH_TOKEN", "GH_REPO", "GITHUB_TOKEN", "NUGET_API_KEY"):
            environment.pop(key, None)
        environment.update(self.workflow_exports)
        if "        env:\n" in block:
            declarations = block.split("        env:\n", 1)[1].split("        run:", 1)[0]
            values = {"${{ inputs.phase }}": "bootstrap", "${{ inputs.recovery_version }}": self.env.get("WORKFLOW_RECOVERY_VERSION", "1.0.0"),
                      "${{ github.token }}": "fixture-github-token", "${{ github.repository }}": "fixture/repo",
                      "${{ secrets.GITHUB_TOKEN }}": "fixture-github-token",
                      "${{ github.sha }}": self.env.get("WORKFLOW_SHA", SHA),
                      "${{ github.ref }}": self.env.get("WORKFLOW_REF", "refs/heads/main"),
                      "${{ steps.nuget-login.outputs.NUGET_API_KEY }}": "fixture-secret-never-print"}
            for line in declarations.splitlines():
                key, value = line.strip().split(": ", 1)
                if "${{" in value:
                    self.assertIn(value, values, f"Unmapped workflow expression for {key}: {value}")
                environment[key] = values.get(value, value)
        command = block.split("        run: ", 1)[1]
        if command.startswith("|\n"):
            command = "\n".join(line[10:] if line else "" for line in command.splitlines()[1:])
        result = subprocess.run(["bash", "-c", command], cwd=self.root,
                                env=environment, text=True, capture_output=True)
        self.assertNotIn("fixture-secret-never-print", result.stdout + result.stderr)
        if environment.get("GITHUB_ENV"):
            github_env = Path(environment["GITHUB_ENV"])
            if github_env.exists():
                self.workflow_exports.update(line.split("=", 1) for line in github_env.read_text().splitlines())
        return result

    def run_workflow_steps(self, job, *names):
        for name in names:
            result = self.run_workflow_step(job, name)
            if result.returncode:
                break
        return result

    def release_calls(self):
        path = self.root / "github-release.log"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def reset_github_release(self, state, *, existing_asset=False):
        (self.root / "github-release.log").unlink(missing_ok=True)
        (self.root / "github-release.json").unlink(missing_ok=True)
        shutil.rmtree(self.root / "github-assets", ignore_errors=True)
        if state != "missing":
            (self.root / "github-release.json").write_text(json.dumps(
                {"isDraft": state == "draft", "assets": [PACKAGE] if existing_asset else []}))
        if existing_asset:
            assets = self.root / "github-assets"
            assets.mkdir()
            (assets / PACKAGE).write_bytes(b"previous release asset")

    def test_workflow_completes_missing_published_and_draft_releases_with_exact_assets(self):
        staged = self.staged()
        unrelated = self.root / "nupkgs/unrelated.nupkg"
        unrelated.write_bytes(b"unrelated artifacts must not become release assets")
        for state, existing_asset, operations in (("missing", False, ["view", "create"]),
                                  ("published", False, ["view", "upload"]),
                                  ("draft", False, ["view", "upload", "edit"]),
                                  ("published", True, ["view", "upload"]),
                                  ("draft", True, ["view", "upload", "edit"])):
            with self.subTest(state=state, existing_asset=existing_asset):
                self.reset_github_release(state, existing_asset=existing_asset)
                result = self.complete_github_release()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual([call[1] for call in self.release_calls()], operations)
                assets = self.root / "github-assets"
                self.assertEqual([path.name for path in assets.iterdir()], [PACKAGE])
                self.assertEqual((assets / PACKAGE).read_bytes(), staged.read_bytes())
                self.assertIs(json.loads((self.root / "github-release.json").read_text())["isDraft"], False)
                self.assertEqual(json.loads((self.root / "github-release.json").read_text())["assets"], [PACKAGE])
                self.assertEqual(unrelated.read_bytes(), b"unrelated artifacts must not become release assets")
                self.assert_no_push()

    def test_workflow_completion_propagates_creation_upload_publication_and_source_failures(self):
        staged = self.staged()
        for failure, state, operations in (("create", "missing", ["view", "create"]),
                                           ("upload", "draft", ["view", "upload"]),
                                           ("edit", "draft", ["view", "upload", "edit"])):
            with self.subTest(failure=failure):
                self.reset_github_release(state)
                self.env["GITHUB_RELEASE_FAIL"] = failure
                result = self.complete_github_release()
                self.assertEqual(result.returncode, 42, result.stderr)
                self.assertIn(f"fixture release {failure} failed", result.stderr)
                self.assertEqual([call[1] for call in self.release_calls()], operations)
                assets = self.root / "github-assets"
                self.assertEqual(assets.exists(), failure == "edit")
                if failure == "edit":
                    self.assertEqual((assets / PACKAGE).read_bytes(), staged.read_bytes())
                if state == "missing":
                    self.assertFalse((self.root / "github-release.json").exists())
                else:
                    self.assertIs(json.loads((self.root / "github-release.json").read_text())["isDraft"], True)
                self.assert_no_push()
        self.env.pop("GITHUB_RELEASE_FAIL")
        self.env["SOURCE_STATE"] = "bootstrap-failed"
        self.reset_github_release("draft")
        result = self.complete_github_release()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No successful latest bootstrap-package.yml push run", result.stderr)
        self.assertEqual(self.release_calls(), [])
        self.assert_no_push()

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
        other = self.root / "nupkgs/other.txt"
        other.parent.mkdir()
        other.write_text("keep")
        for control, commands in (("RESTORE_FAIL", ["restore"]),
                                  ("BUILD_FAIL", ["restore", "build"]),
                                  ("PACK_FAIL", ["restore", "build", "pack"])):
            with self.subTest(control=control):
                self.env[control] = "1"
                (self.root / "dotnet.log").unlink(missing_ok=True)
                result = self.run_script("release-prepare.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual([call[0] for call in self.calls()], commands)
                if control != "PACK_FAIL":
                    self.assertIn(f"fixture production {commands[-1]} failed", result.stderr)
                self.assertEqual(other.read_text(), "keep")
                self.assertFalse((other.parent / "bootstrap").exists())
                self.assertFalse((other.parent / "bootstrap.sha256").exists())
                self.assert_no_push()
                del self.env[control]

    def test_prepare_rejects_invalid_packed_contents_before_consumer_or_receipt(self):
        for invalid, message in (("symbols", f"Expected ['{PACKAGE}'], found ['{PACKAGE}', 'symbols.snupkg']"),
                                 ("dependency", "consumer-visible package dependencies")):
            with self.subTest(invalid=invalid):
                self.env["PACK_INVALID"] = invalid
                (self.root / "dotnet.log").unlink(missing_ok=True)
                result = self.run_script("release-prepare.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual([call[0] for call in self.calls()], ["restore", "build", "pack"])
                self.assertFalse((self.root / "nupkgs/bootstrap").exists())
                self.assertFalse((self.root / "nupkgs/bootstrap.sha256").exists())
                self.assertNotIn("Prepared Hexalith.McpCli.Abstractions", result.stdout)
                self.assert_no_push()

    def test_prepare_rejects_unknown_arguments_before_effects(self):
        for arguments in (("--verify-soruce",), ("--verify-source", "extra")):
            with self.subTest(arguments=arguments):
                result = self.run_script("release-prepare.sh", "1.0.0", *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Usage: release-prepare.sh VERSION [--verify-source]", result.stderr)
                self.assertEqual(self.calls(), [])
                self.assertFalse((self.root / "registry.log").exists())
                self.assertFalse((self.root / "nupkgs").exists())

    def test_publish_rejects_extra_or_missing_arguments_before_effects(self):
        staged = self.staged()
        prepared_bytes = staged.read_bytes()
        for arguments in ((), ("1.0.0", "--dry-run"), ("1.0.0", "extra")):
            with self.subTest(arguments=arguments):
                result = self.run_script("release-publish.sh", *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "Usage: release-publish.sh VERSION\n")
                self.assertEqual(self.calls(), [])
                self.assertFalse((self.root / "registry.log").exists())
                self.assertEqual(staged.read_bytes(), prepared_bytes)
                self.assert_no_push()

    def test_semantic_release_preparation_and_asset_glob_use_the_validated_package(self):
        configuration = json.loads((ROOT / ".releaserc.json").read_text())
        plugins = {plugin[0]: plugin[1] for plugin in configuration["plugins"] if isinstance(plugin, list)}
        command = plugins["@semantic-release/exec"]["prepareCmd"].replace("${nextRelease.version}", "1.0.0")
        result = subprocess.run(command, shell=True, cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified current main source " + SHA, result.stdout)
        self.assertEqual(sorted(path.relative_to(self.root).as_posix()
                                for pattern in plugins["@semantic-release/github"]["assets"]
                                for path in self.root.glob(pattern)), ["nupkgs/bootstrap/" + PACKAGE])
        self.assert_no_push()

    def test_real_git_ignores_prepared_artifacts_and_receipt(self):
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        repository = self.root / "ignore-probe"
        repository.mkdir()
        shutil.copy(ROOT / ".gitignore", repository / ".gitignore")
        real_git = shutil.which("git")
        subprocess.run([real_git, "init", "--quiet", str(repository)], check=True, capture_output=True)
        subprocess.run([real_git, "add", ".gitignore"], cwd=repository, check=True, capture_output=True)
        command = [real_git, "status", "--porcelain", "--untracked-files=normal"]
        before = subprocess.run(command, cwd=repository, check=True, capture_output=True, text=True).stdout
        shutil.copytree(self.root / "nupkgs", repository / "nupkgs")
        after = subprocess.run(command, cwd=repository, check=True, capture_output=True, text=True).stdout
        self.assertEqual(after, before, "Preparation must not add untracked source that blocks publication.")
        self.assertTrue((repository / "nupkgs/bootstrap.sha256").is_file())
        self.assert_no_push()

    def test_prepare_to_publish_uses_the_generated_source_bound_receipt(self):
        for version in ("1.0.0", "1.2.3"):
            with self.subTest(version=version):
                shutil.rmtree(self.root / "nupkgs/bootstrap", ignore_errors=True)
                (self.root / "nupkgs/bootstrap.sha256").unlink(missing_ok=True)
                (self.root / "dotnet.log").unlink(missing_ok=True)
                result = self.run_script("release-prepare.sh", version, "--verify-source")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual([call[0] for call in self.calls()], ["restore", "build", "pack", "restore", "build"])
                for call in self.calls()[:3]:
                    self.assertEqual([arg for arg in call if arg.startswith("-p:Version=")], [f"-p:Version={version}"])
                name = f"Hexalith.McpCli.Abstractions.{version}.nupkg"
                path = self.root / "nupkgs/bootstrap" / name
                self.assertEqual([package.name for package in path.parent.iterdir()], [name])
                expected_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                receipt = json.loads((self.root / "nupkgs/bootstrap.sha256").read_text())
                self.assertEqual(receipt, {"sha256": expected_hash, "source_sha": SHA, "source_clean": True})
                result = self.run_script("release-publish.sh", version)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((self.root / "pushed.sha256").read_text(), expected_hash)
                pushes = [call for call in self.calls() if call[:2] == ["nuget", "push"]]
                self.assertEqual(len(pushes), 1)
                self.assertEqual(Path(pushes[0][2]).name, name)

    def test_dirty_preparation_cannot_publish_or_recover_after_source_is_cleaned(self):
        self.env["LOCAL_SOURCE_STATE"] = "dirty"
        self.env["AFTER_PACK_SOURCE_STATE"] = "clean"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.root / "nupkgs/bootstrap.sha256").read_text())
        self.assertIs(receipt["source_clean"], False)
        shutil.copy(self.root / "nupkgs/bootstrap" / PACKAGE, self.root / "public.nupkg")
        for script, args, state in (("release-publish.sh", ("1.0.0",), "free"),
                             ("recover-bootstrap-release.py", ("1.0.0", "bootstrap"), "free"),
                             ("recover-bootstrap-release.py", ("1.0.0", "bootstrap"), "taken")):
            with self.subTest(script=script, state=state):
                self.env["REGISTRY_STATE"] = state
                result = self.run_script(script, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("receipt records dirty source", result.stderr)
                self.assert_no_push()

    def test_source_becoming_dirty_during_preparation_cannot_publish(self):
        self.env["AFTER_PACK_SOURCE_STATE"] = "dirty"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.root / "nupkgs/bootstrap.sha256").read_text())
        self.assertIs(receipt["source_clean"], False)
        (self.root / "local-source-state").write_text("clean")
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt records dirty source", result.stderr)
        self.assert_no_push()

    def test_older_preparation_cannot_publish_or_recover_from_new_green_source(self):
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.env.update(LOCAL_HEAD_SHA="b" * 40, LIVE_SHA="b" * 40, DISPATCH_SHA="b" * 40,
                        TAG_SHA="b" * 40, REMOTE_TAG_SHA="b" * 40, RUN_SHA="b" * 40)
        shutil.copy(self.root / "nupkgs/bootstrap" / PACKAGE, self.root / "public.nupkg")
        for script, args, state in (("release-publish.sh", ("1.0.0",), "free"),
                             ("recover-bootstrap-release.py", ("1.0.0", "bootstrap"), "free"),
                             ("recover-bootstrap-release.py", ("1.0.0", "bootstrap"), "taken")):
            with self.subTest(script=script, state=state):
                self.env["REGISTRY_STATE"] = state
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

    def test_preparation_requires_an_exact_source_head_before_building(self):
        self.env["LOCAL_HEAD_SHA"] = "invalid"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Preparation requires an exact source SHA.", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.root / "nupkgs").exists())
        self.assert_no_push()

    def test_invalid_requests_are_rejected_by_every_entry_point_before_effects(self):
        for script in ("release-prepare.sh", "release-preflight.sh", "release-publish.sh", "recover-bootstrap-release.py",
                       "smoke-bootstrap-consumer.sh"):
            for phase, version, message in (("paired", "1.0.0", "deferred"), ("unknown", "1.0.0", "Unknown"),
                    ("-h", "1.0.0", "Unknown"),
                    *(("bootstrap", version, "Invalid") for version in (
                        "-h", "1.0", "01.0.0", "1.0.0-", "1.0.0-01", "1.0.0-a..b", "1.0.0+meta", "1.0.0\n",
                        "2147483648.0.0", "0.2147483648.0", "0.0.2147483648"))):
                with self.subTest(script=script, phase=phase, version=version):
                    if script == "smoke-bootstrap-consumer.sh" and phase != "bootstrap":
                        continue  # Consumer smoke always validates the bootstrap phase.
                    self.env["MCPCLI_RELEASE_PHASE"] = phase
                    arguments = ((version, "source", "consumer") if script == "smoke-bootstrap-consumer.sh" else
                                 ("--", version, phase) if script.endswith(".py") else (version,))
                    result = self.run_script(script, *arguments)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertEqual(self.calls(), [])
                    self.assert_no_push()
                    self.assertFalse((self.root / "registry.log").exists())
                    self.assertFalse((self.root / "gh.log").exists())
                    self.assertFalse((self.root / "nupkgs").exists())
                    self.assertFalse((self.root / "consumer").exists())

    def test_option_like_source_identifiers_cannot_skip_receipt_or_source_checks(self):
        self.staged()
        for key, message in (("DISPATCH_SHA", "receipt source SHA does not match"),
                             ("DISPATCH_REF", "Release must be dispatched from refs/heads/main")):
            with self.subTest(key=key):
                original = self.env[key]
                self.env[key] = "-h"
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertNotIn("usage:", result.stdout)
                self.assert_no_push()
                self.env[key] = original

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
        for state in ("taken", "404", "403", "500", "timeout", "bad-json", "bad-shape", "empty", "unexpected-status",
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
                if name == "subdirectory":
                    extra.mkdir()
                else:
                    extra.write_text("unexpected")
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Expected", result.stderr)
                self.assert_no_push()
                if extra.is_dir():
                    extra.rmdir()
                else:
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
        valid = json.loads(receipt.read_text())
        malformed = [{key: value for key, value in valid.items() if key != "source_clean"},
                     dict(valid, extra="unexpected"), dict(valid, source_clean=1),
                     dict(valid, sha256="invalid"), dict(valid, source_sha="invalid")]
        for contents in (None, "invalid", "a" * 64, *(json.dumps(value) for value in malformed)):
            with self.subTest(contents=contents):
                if contents is None:
                    receipt.unlink()
                else:
                    receipt.write_text(contents)
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("The prepared bootstrap package hash receipt is " +
                              ("missing or invalid." if contents is None else "invalid."), result.stderr)
                self.assertNotIn("Traceback", result.stderr)
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
            "Hexalith.McpCli.nuspec": '<package><metadata><id>Hexalith.McpCli</id><version>1.0.0</version>'
                + ('<packageTypes><packageType name="DotnetTool" /></packageTypes>' if package_type else '')
                + '</metadata></package>',
            "README.md": "fixture", prefix + "Hexalith.McpCli.dll": bytes(managed),
            prefix + "Hexalith.McpCli.deps.json": json.dumps({"runtimeTarget": {"name": ".NETCoreApp,Version=v10.0"}, "libraries": {"Sample.Contracts/1.0.0": {}}, "targets": {".NETCoreApp,Version=v10.0": {"Sample.Contracts/1.0.0": {}}}}),
            prefix + "Hexalith.McpCli.runtimeconfig.json": json.dumps({"runtimeOptions": {"tfm": "net10.0", "framework": {"name": "Microsoft.NETCore.App", "version": "10.0.0"}}}),
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

    def test_paired_validator_rejects_runtime_and_enrollment_drift(self):
        self.staged()
        prefix = 'tools/net10.0/any/'
        cases = [
            (prefix + 'Hexalith.McpCli.dll', b'native payload', 'managed PE'),
            (prefix + 'Hexalith.McpCli.deps.json', json.dumps({'runtimeTarget': {'name': '.NETCoreApp,Version=v10.0/linux-x64'}}), 'portable .NET 10'),
            (prefix + 'Hexalith.McpCli.deps.json', json.dumps({'runtimeTarget': {'name': '.NETCoreApp,Version=v10.0'}, 'libraries': {}}), 'Packaged Contracts versions'),
            (prefix + 'Hexalith.McpCli.runtimeconfig.json', json.dumps({'runtimeOptions': {'tfm': 'net10.0', 'includedFrameworks': [{'name': 'Microsoft.NETCore.App'}]}}), 'framework-dependent'),
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
                result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()
        self.paired_tool()
        (self.root / 'tools/dependency-policy.json').write_text(json.dumps({'modules': {'Sample.Contracts': '2.0.0'}}))
        result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Restored Contracts versions', result.stderr)
        self.paired_tool()
        (self.root / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj').write_text('<Project />')
        result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Generated manifest, flagged Contracts references', result.stderr)
        self.assert_no_push()

    def test_paired_validator_refuses_native_files_and_native_dependency_entries(self):
        self.staged()
        self.paired_tool()
        prefix = 'tools/net10.0/any/'
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
            ('tools/net10.0/win-x64/payload.exe', b'MZnative', 'Alternate tools layouts'),
            ('tools/net9.0/any/readme.txt', b'alternate', 'Alternate tools layouts'),
            ('content/native-host.bin', b'MZnative', 'executable payload'),
            ('content/native.exe', b'native', 'Native payload'),
            ('content/libnative.so', b'native', 'Native payload'),
            ('content/elf.bin', b'\x7fELF' + bytes(12), 'Native payload'),
        ])
        for kind, assets in [('native', {'extra.so': {}}),
                             ('runtimeTargets', {'runtimes/linux-x64/native/extra.so': {'assetType': 'native', 'rid': 'linux-x64'}})]:
            deps = json.loads(base[prefix + 'Hexalith.McpCli.deps.json'])
            deps['targets']['.NETCoreApp,Version=v10.0']['Sample.Contracts/1.0.0'][kind] = assets
            cases.append((prefix + 'Hexalith.McpCli.deps.json', json.dumps(deps), 'Native'))
        for name, payload, message in cases:
            with self.subTest(name=name, message=message):
                with ZipFile(path, 'w') as archive:
                    files = {**base, name: payload}
                    for item, contents in files.items(): archive.writestr(item, contents)
                result = self.run_script('validate-release-packages.py', str(path.parent), '1.0.0', 'paired')
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

    def test_prepare_refuses_an_existing_regular_receipt_without_staging(self):
        receipt = self.root / "nupkgs/bootstrap.sha256"
        receipt.parent.mkdir()
        receipt.write_text("preserved receipt")
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Bootstrap staging or its receipt already exists", result.stderr)
        self.assertEqual(receipt.read_text(), "preserved receipt")
        self.assertFalse((receipt.parent / "bootstrap").exists())
        self.assertEqual(self.calls(), [])
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

    def test_consumer_preserves_url_sources_in_config_restore_and_build(self):
        source = "https://api.nuget.org/v3/index.json"
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", source, "consumer")
        self.assertEqual(result.returncode, 0, result.stderr)
        from xml.etree import ElementTree
        config = ElementTree.fromstring((self.root / "consumer-nuget.config").read_text())
        self.assertEqual(config.find("packageSources/add").attrib["value"], source)
        self.assertEqual([call[0] for call in self.calls()], ["restore", "build"])
        for call in self.calls():
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
        for call in self.calls():
            for option in ("ImportDirectoryBuildProps", "ImportDirectoryBuildTargets", "ImportDirectoryPackagesProps"):
                self.assertIn(f"-p:{option}=false", call)
        self.assert_no_push()

    def test_consumer_disables_terminal_logger_even_when_forced(self):
        self.env["MSBUILDTERMINALLOGGER"] = "on"
        result = self.run_script("smoke-bootstrap-consumer.sh", "1.0.0", "/selected/source", "consumer")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[0] for call in self.calls()], ["restore", "build"])
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

    def test_failed_consumer_smoke_prevents_preparation_receipt(self):
        self.env["SMOKE_FAIL"] = "1"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "nupkgs/bootstrap.sha256").exists())
        self.assertFalse((self.root / "nupkgs/bootstrap").exists())
        self.assert_no_push()

    def test_package_mutation_during_consumer_build_prevents_preparation_receipt(self):
        self.env["SMOKE_MUTATE_PACKAGE"] = "1"
        result = self.run_script("release-prepare.sh", "1.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("The bootstrap package changed during the consumer build.", result.stderr)
        self.assertEqual([call[0] for call in self.calls()], ["restore", "build", "pack", "restore", "build"])
        self.assertFalse((self.root / "nupkgs/bootstrap.sha256").exists())
        self.assertFalse((self.root / "nupkgs/bootstrap").exists())
        self.assert_no_push()

    def test_analyzer_diagnostic_rejections_prevent_preparation_receipt(self):
        for output, message in (("missing-diagnostic", "did not report MCPCLI001 on MissingDescriptionQuery.cs"),
                                ("wrong-file", "did not report MCPCLI001 on MissingDescriptionQuery.cs"),
                                ("extra-warning", "must report exactly one warning"),
                                ("load-failure", "packaged analyzer could not load"),
                                ("newer-analyzer", "packaged analyzer could not load")):
            with self.subTest(output=output):
                self.env["SMOKE_OUTPUT"] = output
                result = self.run_script("release-prepare.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "nupkgs/bootstrap.sha256").exists())
                self.assertFalse((self.root / "nupkgs/bootstrap").exists())
                self.assertIn(message, result.stderr)
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
        for state, message in (("not-git", "returned non-zero exit status 128"),
                               ("wrong-head", "Checked-out HEAD does not match the exact release source SHA"),
                               ("feature", "Checked-out source must be main or its exact detached SHA"),
                               ("dirty", "Release source has uncommitted changes"),
                               ("untracked", "Release source has uncommitted changes")):
            with self.subTest(state=state):
                self.env["LOCAL_SOURCE_STATE"] = state
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()
        self.env["LOCAL_SOURCE_STATE"] = "clean"
        for state, message in (("stale", "Dispatch SHA is not the current main SHA"),
                               ("bootstrap-failed", "No successful latest bootstrap-package.yml push run"),
                               ("commitlint-missing", "No successful latest commitlint.yml push run")):
            with self.subTest(state=state):
                self.env["SOURCE_STATE"] = state
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()

    def test_recovery_publishes_absent_package_then_verifies_public_content(self):
        staged = self.staged()
        shutil.copy(staged, self.root / "public.nupkg")
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified public package", result.stdout)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 1)

    def test_recover_workflow_preserves_scripts_checks_out_tag_and_uses_login_key(self):
        runner = self.root / "runner-temp"
        runner.mkdir()
        github_env = runner / "github-env"
        github_env.touch()
        self.env.update(LIVE_SHA="b" * 40, LOCAL_HEAD_SHA="b" * 40, DISPATCH_SHA="b" * 40,
                        REMOTE_TAG_ANNOTATED="1", SABOTAGE_TAGGED_SCRIPTS="1",
                        RUNNER_TEMP=str(runner), GITHUB_ENV=str(github_env),
                        NUGET_API_KEY="ambient-key-must-not-be-used",
                        EXPECTED_PUBLICATION_KEY="fixture-secret-never-print")
        for name in ("Preserve reviewed recovery scripts before checking out the release tag",
                     "Require an existing release tag on main",
                     "Rebuild and consumer-test the tagged package",
                     "Publish only if absent and verify the public package",
                     "Complete the GitHub release"):
            with self.subTest(step=name):
                result = self.run_workflow_step("recover", name)
                self.assertEqual(result.returncode, 0, result.stderr)
                if name == "Require an existing release tag on main":
                    self.assertEqual(github_env.read_text(), f"DISPATCH_SHA={SHA}\n")
                    self.assertEqual(self.workflow_exports, {"DISPATCH_SHA": SHA})
                    self.assertEqual(self.env["DISPATCH_SHA"], "b" * 40)
                elif name == "Rebuild and consumer-test the tagged package":
                    shutil.copy(self.root / "nupkgs/bootstrap" / PACKAGE, self.root / "public.nupkg")
                elif name == "Publish only if absent and verify the public package":
                    self.assertIn("Verified tagged recovery source", result.stdout)
                    self.assertIn("Verified public package", result.stdout)
        self.assertFalse((self.root / "tagged-helper.log").exists())
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 1)
        self.assertEqual([call[1] for call in self.release_calls()], ["view", "create"])
        self.assertEqual((self.root / "github-assets" / PACKAGE).read_bytes(),
                         (self.root / "nupkgs/bootstrap" / PACKAGE).read_bytes())

    def test_publication_workflow_uses_nuget_login_output_instead_of_ambient_key(self):
        self.env["NUGET_API_KEY"] = "ambient-key-must-not-be-used"
        self.env["DISPATCH_SHA"] = "ambient-sha-must-not-be-used"
        self.env["EXPECTED_PUBLICATION_KEY"] = "fixture-secret-never-print"
        shutil.copy(ROOT / ".releaserc.json", self.root / ".releaserc.json")
        self.executable("npx", '''#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
if sys.argv[1:] != ["--no-install", "semantic-release"]: sys.exit(1)
Path(os.environ["RELEASE_TEST_ROOT"]).joinpath("semantic-release-key").write_text(os.environ["NUGET_API_KEY"])
configuration = json.loads(Path(".releaserc.json").read_text())
hooks = next(plugin[1] for plugin in configuration["plugins"]
             if isinstance(plugin, list) and plugin[0] == "@semantic-release/exec")
for name in ("verifyReleaseCmd", "prepareCmd", "publishCmd"):
    command = hooks[name].replace("${nextRelease.version}", "1.0.0")
    subprocess.run(command, shell=True, check=True)
''')
        result = self.run_workflow_step("publish", "Derive one version and publish the selected phase")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "semantic-release-key").read_text(), "fixture-secret-never-print")
        self.assertEqual(result.stdout.count("Verified current main source " + SHA), 2)
        staged = self.root / "nupkgs/bootstrap" / PACKAGE
        expected_hash = hashlib.sha256(staged.read_bytes()).hexdigest()
        self.assertEqual((self.root / "pushed.sha256").read_text(), expected_hash)
        self.assertEqual(json.loads((self.root / "nupkgs/bootstrap.sha256").read_text()),
                         {"sha256": expected_hash, "source_sha": SHA, "source_clean": True})
        self.assertEqual([call[0] for call in self.calls()], ["restore", "build", "pack", "restore", "build", "nuget"])
        push, = [call for call in self.calls() if call[:2] == ["nuget", "push"]]
        self.assertEqual(Path(push[2]).name, PACKAGE)
        self.assertEqual(len((self.root / "registry.log").read_text().splitlines()), 2)

    def test_push_failures_stop_direct_publication_recovery_and_workflow_completion(self):
        self.staged()
        self.env["PUSH_FAIL"] = "1"
        preserved = self.root / "runner-temp/release-scripts"
        shutil.copytree(self.root / "scripts", preserved)
        self.env["RUNNER_TEMP"] = str(preserved.parent)
        self.workflow_exports["DISPATCH_SHA"] = SHA
        for entry in ("direct", "recovery", "workflow"):
            with self.subTest(entry=entry):
                (self.root / "dotnet.log").unlink(missing_ok=True)
                if entry == "direct":
                    result = self.run_script("release-publish.sh", "1.0.0")
                    self.assertEqual(result.returncode, 43)
                elif entry == "recovery":
                    result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
                else:
                    result = self.run_workflow_steps("recover", "Publish only if absent and verify the public package",
                                                     "Complete the GitHub release")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("fixture NuGet push failed: HTTP 403", result.stderr)
                self.assertNotIn("Verified public package", result.stdout)
                self.assertEqual(len(self.calls()), 1)
                self.assertEqual(self.calls()[0][:2], ["nuget", "push"])
                self.assertFalse((self.root / "pushed.sha256").exists())
                self.assertFalse((self.root / "downloads.log").exists())
                self.assertFalse((self.root / "consumer-environment.json").exists())
                self.assertEqual(self.release_calls(), [])

    def test_recovery_rejects_invalid_source_before_registry_download_or_consumer_calls(self):
        shutil.copy(self.staged(), self.root / "public.nupkg")
        self.env["REGISTRY_STATE"] = "taken"
        for key, value, message in (("LOCAL_SOURCE_STATE", "dirty", "Release source has uncommitted changes"),
                                    ("SOURCE_STATE", "bootstrap-failed", "No successful latest bootstrap-package.yml push run"),
                                    ("DISPATCH_REF", "refs/heads/feature", "Release must be dispatched from refs/heads/main")):
            with self.subTest(key=key):
                original = self.env.get(key)
                self.env[key] = value
                result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse((self.root / "registry.log").exists())
                self.assertFalse((self.root / "downloads.log").exists())
                self.assertEqual(self.calls(), [])
                self.assertNotIn("Verified public package", result.stdout)
                self.assert_no_push()
                if original is None:
                    del self.env[key]
                else:
                    self.env[key] = original

    def test_workflow_tag_step_refuses_missing_or_unmerged_tags_before_building(self):
        self.env.update(RECOVERY_VERSION="1.0.0", RECOVERY_PHASE="bootstrap")
        for changed, value, message in (("TAG_EXISTS", "false", "does not exist"),
                                       ("RECOVERY_ANCESTOR", "false", "not on main"),
                                       ("WORKFLOW_RECOVERY_VERSION", "invalid", "Invalid release version: invalid")):
            with self.subTest(changed=changed):
                self.env[changed] = value
                result = self.run_workflow_step("recover", "Require an existing release tag on main")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse((self.root / "checkout-sha").exists())
                self.assertEqual(self.calls(), [])
                del self.env[changed]

    def test_recovery_waits_for_its_newly_pushed_package_after_a_404(self):
        shutil.copy(self.staged(), self.root / "public.nupkg")
        self.env["PUBLIC_STATE"] = "404-then-200"
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Waiting for the pushed package to become public", result.stdout)
        self.assertIn("Verified public package", result.stdout)
        self.assertEqual(len((self.root / "downloads.log").read_text().splitlines()), 2)
        self.assertEqual((self.root / "sleeps.log").read_text().splitlines(), ["10"])
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 1)

    def test_recovery_reports_local_package_write_failure_without_registry_error(self):
        shutil.copy(self.staged(), self.root / "public.nupkg")
        self.env.update(REGISTRY_STATE="taken", PUBLIC_WRITE_FAIL="1")
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Bootstrap recovery failed: fixture: No space left on device", result.stderr)
        self.assertNotIn("uncertain registry response", result.stderr)
        self.assertEqual(len((self.root / "downloads.log").read_text().splitlines()), 1)
        self.assertFalse((self.root / "sleeps.log").exists())
        self.assertEqual(self.calls(), [])
        self.assert_no_push()

    def test_recovery_public_download_diagnostics_preserve_only_status_or_exception_type(self):
        shutil.copy(self.staged(), self.root / "public.nupkg")
        self.env["REGISTRY_STATE"] = "taken"
        for state, detail in (("404", "HTTP 404"), ("500", "HTTP 500"),
                              ("timeout", "TimeoutError"), ("url-error", "URLError"),
                              ("unexpected-status", "HTTP 201")):
            with self.subTest(state=state):
                self.env["PUBLIC_STATE"] = state
                (self.root / "downloads.log").unlink(missing_ok=True)
                result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"Could not verify the public package: uncertain registry response ({detail})", result.stderr)
                self.assertEqual(len((self.root / "downloads.log").read_text().splitlines()), 1)
                self.assertEqual(self.calls(), [])
                self.assertFalse((self.root / "consumer-environment.json").exists())
                self.assertNotIn("Verified public package", result.stdout)
                self.assert_no_push()

    def test_recovery_processing_wait_is_bounded_and_only_retries_new_package_404s(self):
        shutil.copy(self.staged(), self.root / "public.nupkg")
        for registry, public, downloads, sleeps, pushes in (("free", "404", 91, 90, 1),
                                                          ("taken", "404", 1, 0, 0),
                                                          ("free", "500", 1, 0, 1),
                                                          ("free", "timeout", 1, 0, 1)):
            with self.subTest(registry=registry, public=public):
                self.env.update(REGISTRY_STATE=registry, PUBLIC_STATE=public)
                for name in ("downloads.log", "sleeps.log", "dotnet.log"):
                    (self.root / name).unlink(missing_ok=True)
                result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Could not verify the public package", result.stderr)
                self.assertEqual(len((self.root / "downloads.log").read_text().splitlines()), downloads)
                sleep_log = self.root / "sleeps.log"
                self.assertEqual(len(sleep_log.read_text().splitlines()) if sleep_log.exists() else 0, sleeps)
                self.assertEqual(sum(int(delay) for delay in sleep_log.read_text().splitlines()) if sleep_log.exists() else 0,
                                 900 if sleeps else 0)
                self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), pushes)

    def test_recovery_requires_consumer_analyzer_proof_from_the_download_directory(self):
        shutil.copy(self.staged(), self.root / "public.nupkg")
        self.env.update(REGISTRY_STATE="taken", SMOKE_FAIL="1")
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Verified public package", result.stdout)
        restore, = self.calls()
        self.assertEqual(restore[0], "restore")
        source, = [option.split("=", 1)[1] for option in restore if option.startswith("-p:RestoreSources=")]
        self.assertEqual(Path(source).name, "public")
        self.assertNotEqual(Path(source), self.root / "nupkgs/bootstrap")
        self.assert_no_push()

    def test_recovery_rejects_source_becoming_dirty_during_public_consumer_build(self):
        shutil.copy(self.staged(), self.root / "public.nupkg")
        source_state = self.root / "local-source-state"
        source_state.write_text("clean")
        self.env.update(REGISTRY_STATE="taken", AFTER_CONSUMER_SOURCE_STATE="dirty")
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Release source has uncommitted changes.", result.stderr)
        self.assertNotIn("Verified public package", result.stdout)
        self.assertEqual(source_state.read_text(), "dirty")
        self.assertEqual([call[0] for call in self.calls()], ["restore", "build"])
        self.assert_no_push()

    def test_recovery_rejects_changed_compile_bytes_with_identical_entry_names(self):
        staged = self.staged()
        with ZipFile(staged) as prepared, ZipFile(self.root / "public.nupkg", "w") as archive:
            for name in prepared.namelist():
                archive.writestr(name, b"changed compile bytes" if name.startswith("lib/") else prepared.read(name))
        self.env["REGISTRY_STATE"] = "taken"
        result = self.run_script("recover-bootstrap-release.py", "1.0.0", "bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content does not match", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assert_no_push()

    def test_tagged_recovery_rejects_wrong_tag_moved_main_nonancestor_and_failed_gate(self):
        self.staged()
        self.env["LIVE_SHA"] = "b" * 40
        for changed, value, message in (("TAG_SHA", "c" * 40, "Recovery tag does not match"),
                                        ("REMOTE_TAG_SHA", "c" * 40, "Remote recovery tag does not match"),
                                        ("REMOTE_TAG_TYPE", "tree", "Remote recovery tag does not resolve to a commit."),
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

    def test_direct_recovery_publish_requires_tagged_source_and_independent_gates(self):
        self.staged()
        # Main is ahead of the tag, so only the tagged-recovery source policy can pass.
        self.env.update(MCPCLI_RECOVERY_VERSION="1.0.0", LIVE_SHA="b" * 40)
        baseline = dict(self.env)
        for changed, value, message in (("RECOVERY_ANCESTOR", "false", "Recovery tag is not an ancestor of current main"),
                                        ("REMOTE_TAG_SHA", "c" * 40, "Remote recovery tag does not match the exact release SHA"),
                                        ("SOURCE_STATE", "bootstrap-failed", "No successful latest bootstrap-package.yml push run")):
            with self.subTest(changed=changed):
                self.env = dict(baseline, **{changed: value})
                result = self.run_script("release-publish.sh", "1.0.0")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assert_no_push()
        self.env = baseline
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified tagged recovery source", result.stdout)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["nuget", "push"]]), 1)

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
        staged = self.staged(core_properties="original packing NuGet version")
        with ZipFile(staged) as prepared, ZipFile(self.root / "public.nupkg", "w") as archive:
            for name in prepared.namelist():
                contents = (b"different packing NuGet version" if name.endswith(".psmdcp") else prepared.read(name))
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
        for state in ("404", "timeout", "500", "bad-json", "nonsense-version"):
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
        self.env["REGISTRY_STATE"] = "free"
        result = self.run_script("release-publish.sh", "1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "pushed.sha256").read_text(), expected)
        pushed = Path((self.root / "pushed.path").read_text())
        self.assertNotEqual(pushed.parent, path.parent)
        self.assertFalse(pushed.exists())  # Private snapshot is cleaned after push.
        self.assertEqual(len(self.calls()), 1)
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
                                ("missing", "failed", "pending", "other-sha", "other-branch", "pull-request", "rerun-failed"))):
            with self.subTest(state=state):
                self.env["SOURCE_STATE"] = state
                result = self.run_script("verify-release-source.py", SHA, "refs/heads/main", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                message = ("Dispatch SHA is not the current main SHA" if state == "stale" else
                           f"No successful latest {'bootstrap-package.yml' if state.startswith('bootstrap-') else 'commitlint.yml'} push run exists for {SHA}")
                self.assertIn(message, result.stderr)
                self.assert_no_push()

    def test_source_gate_requires_no_full_tool_ci_or_module_prerequisite(self):
        result = self.run_script("verify-release-source.py", SHA, "refs/heads/main", "bootstrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.root / "gh.log").read_text()
        self.assertIn("bootstrap-package.yml", calls)
        self.assertIn("commitlint.yml", calls)
        self.assertNotIn("/ci.yml", calls)
        self.assert_no_push()

    def test_source_gate_reports_sanitized_subprocess_stderr_and_redacts_known_credentials(self):
        self.env.update(GH_TOKEN="fixture-gh-token", GITHUB_TOKEN="fixture-gh-token-longer",
                        GH_ENTERPRISE_TOKEN="fixture-enterprise-token", GITHUB_ENTERPRISE_TOKEN="fixture-enterprise-other")
        credentials = [self.env[name] for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN",
                                                  "GITHUB_ENTERPRISE_TOKEN", "NUGET_API_KEY")]
        self.env["SUBPROCESS_STDERR"] = "HTTP 403: Resource not accessible by integration\x1b\ncredentials: " + " ".join(credentials)
        for source, local in (("permission-denied", "clean"), ("success", "not-git")):
            with self.subTest(source=source, local=local):
                self.env.update(SOURCE_STATE=source, LOCAL_SOURCE_STATE=local)
                result = self.run_script("verify-release-source.py", SHA, "refs/heads/main", "bootstrap")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("HTTP 403: Resource not accessible by integration", result.stderr)
                self.assertEqual(result.stderr.count("[REDACTED]"), len(credentials))
                for credential in credentials:
                    self.assertNotIn(credential, result.stderr)
                self.assertNotIn("\x1b", result.stderr)
                self.assertNotIn("\x00", result.stderr)
                self.assert_no_push()

    def test_source_gate_accepts_exact_detached_head_for_release_and_recovery(self):
        self.env["LOCAL_SOURCE_STATE"] = "detached"
        for arguments in ((), ("--tagged-recovery", "1.0.0")):
            with self.subTest(arguments=arguments):
                result = self.run_script("verify-release-source.py", SHA, "refs/heads/main", "bootstrap", *arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Verified tagged recovery source" if arguments else "Verified current main source", result.stdout)
                self.assert_no_push()

    def test_workflow_checks_source_before_both_production_modes_and_separates_bootstrap_events(self):
        release = (ROOT / ".github/workflows/release.yml").read_text()
        verify = release.split("  verify-source:\n", 1)[1].split("  publish:\n", 1)[0]
        self.assertIn("    if: ${{ inputs.phase != 'stage-paired' }}", verify)
        for job in ("publish", "recover"):
            section = release.split(f"  {job}:\n", 1)[1].split("    steps:\n", 1)[0]
            self.assertIn("    needs: verify-source\n", section)
            operator = "==" if job == "publish" else "!="
            self.assertIn(f"    if: ${{{{ inputs.recovery_version {operator} '' }}}}\n", section)
        self.assertIn('run: bash "$RUNNER_TEMP/release-scripts/release-prepare.sh" "$RECOVERY_VERSION"', release)
        bootstrap = (ROOT / ".github/workflows/bootstrap-package.yml").read_text()
        self.assertIn("group: bootstrap-package-${{ github.event_name }}-${{ github.ref }}", bootstrap)

    def test_workflow_source_steps_reject_stale_main_and_failed_bootstrap_before_effects(self):
        for job, name in (("verify-source", "Require current main with exact-source bootstrap and commitlint success"),
                          ("publish", "Recheck source and independent results after production approval"),
                          ("recover", "Require current reviewed recovery workflow and independent gates")):
            for state, message in (("stale", "Dispatch SHA is not the current main SHA"),
                                   ("bootstrap-failed", f"No successful latest bootstrap-package.yml push run exists for {SHA}")):
                with self.subTest(job=job, state=state):
                    self.env["SOURCE_STATE"] = state
                    result = self.run_workflow_step(job, name)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertEqual(self.calls(), [])
                    self.assertEqual(self.release_calls(), [])
                    self.assertFalse((self.root / "registry.log").exists())
                    self.assert_no_push()

    def test_workflow_source_steps_require_their_own_sha_declarations(self):
        from unittest.mock import patch
        self.env["DISPATCH_SHA"] = SHA
        for job, name in (("verify-source", "Require current main with exact-source bootstrap and commitlint success"),
                          ("publish", "Recheck source and independent results after production approval"),
                          ("recover", "Require current reviewed recovery workflow and independent gates")):
            with self.subTest(job=job):
                result = self.run_workflow_step(job, name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Verified current main source " + SHA, result.stdout)
                block = self.workflow_step(job, name)
                declaration = "          DISPATCH_SHA: ${{ github.sha }}\n"
                self.assertIn(declaration, block)
                with patch.object(self, "workflow_step", return_value=block.replace(declaration, "")):
                    result = self.run_workflow_step(job, name)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Release requires an exact source SHA", result.stderr)
                self.assertEqual(self.calls(), [])
                self.assertEqual(self.release_calls(), [])
                self.assertFalse((self.root / "registry.log").exists())
                self.assert_no_push()

    def test_workflow_harness_rejects_unmapped_expressions(self):
        from unittest.mock import patch
        with patch.object(self, "workflow_step", return_value=(
                "        env:\n          GH_TOKEN: ${{ steps.wrong.outputs.token }}\n        run: true")):
            with self.assertRaisesRegex(AssertionError, "Unmapped workflow expression for GH_TOKEN"):
                self.run_workflow_step("recover", "fixture")
        self.assertEqual(self.calls(), [])
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
