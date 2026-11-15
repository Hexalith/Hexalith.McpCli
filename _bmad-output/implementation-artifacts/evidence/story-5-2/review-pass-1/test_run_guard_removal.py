"""Process controls for the runner's kill, survivor and error classifications."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).with_name("run_guard_removal.py")
EVIDENCE = Path("_bmad-output/implementation-artifacts/evidence/story-5-2")
MAP = Path("_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-capability-class-map.json")


class RunnerProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.evidence = self.root / EVIDENCE
        self.evidence.mkdir(parents=True)
        runner = self.evidence / "review-pass-1/run_guard_removal.py"
        runner.parent.mkdir()
        shutil.copyfile(RUNNER, runner)
        self.runner = runner
        (self.root / MAP).parent.mkdir(parents=True)
        (self.root / MAP).write_text(json.dumps({
            "decision": {"path": "decision.md"}, "approvalPath": "approval.json", "inventories": [],
        }))
        (self.root / "decision.md").write_text("fixture\n")
        (self.root / "approval.json").write_text("{}\n")
        (self.evidence / "verifier.stdout.txt").write_text("fixture\n")
        self.verifier = self.evidence / "verify_class_map.py"
        self.verifier.write_text(
            "def require(condition, message):\n"
            "    if not condition:\n"
            "        raise ValueError(message)\n"
            "\ndef selected():\n"
            "    require(False, 'blocked')\n"
            "    return True\n"
        )
        self.original_hash = hashlib.sha256(self.verifier.read_bytes()).hexdigest()

    def run_control(self, action, *, baseline_action=""):
        (self.evidence / "test_verify_class_map.py").write_text(
            "import runpy\nimport sys\nimport time\nimport unittest\nfrom pathlib import Path\n"
            "assert __name__ == '__main__', 'execute the supported test module directly'\n"
            "selected = runpy.run_path(str(Path(__file__).with_name('verify_class_map.py')))['selected']\n"
            "class GuardCase(unittest.TestCase):\n"
            "    def test_guard(self):\n"
            + "".join(f"        {line}\n" for line in baseline_action.splitlines())
            + "        try:\n            selected()\n        except ValueError:\n            return\n"
            + "".join(f"        {line}\n" for line in action.splitlines())
            + "if __name__ == '__main__':\n    unittest.main()\n"
        )
        output = self.root / "results"
        process = subprocess.run(
            [sys.executable, "-I", "-B", str(self.runner), "--output", str(output),
             "--jobs", "1", "--timeout-seconds", "1"],
            capture_output=True, check=False, timeout=10,
        )
        self.assertEqual(b"", process.stderr)
        receipt = json.loads((output / "results.json").read_bytes())
        return process, receipt, output

    def test_assertion_failure_kills_guard_and_exits_zero(self):
        process, receipt, _ = self.run_control("self.fail('guard removed')")
        self.assertEqual(0, process.returncode)
        self.assertEqual({"guardCount": 1, "killed": 1, "survived": 0, "error": 0}, receipt["summary"])
        guard = receipt["guards"][0]
        self.assertEqual(1, len(guard["assertionFailures"]))
        self.assertEqual([], guard["testErrors"])

    def test_survivor_is_reported_and_exits_one(self):
        process, receipt, _ = self.run_control("return")
        self.assertEqual(1, process.returncode)
        self.assertEqual({"guardCount": 1, "killed": 0, "survived": 1, "error": 0}, receipt["summary"])
        self.assertEqual("survived", receipt["guards"][0]["outcome"])

    def test_unittest_error_is_never_a_kill_and_exits_one(self):
        process, receipt, _ = self.run_control("raise RuntimeError('control error')")
        self.assertEqual(1, process.returncode)
        self.assertEqual({"guardCount": 1, "killed": 0, "survived": 0, "error": 1}, receipt["summary"])
        guard = receipt["guards"][0]
        self.assertEqual([], guard["assertionFailures"])
        self.assertEqual(1, len(guard["testErrors"]))
        self.assertTrue(guard["completedSuite"])

    def test_incomplete_zero_exit_is_error(self):
        process, receipt, _ = self.run_control("__import__('os')._exit(0)")
        self.assertEqual(1, process.returncode)
        self.assertEqual("error", receipt["guards"][0]["outcome"])
        self.assertFalse(receipt["guards"][0]["completedSuite"])

    def test_assertion_plus_unittest_error_is_still_error(self):
        process, receipt, _ = self.run_control(
            "with self.subTest():\n    self.fail('guard removed')\nraise RuntimeError('control error')"
        )
        self.assertEqual(1, process.returncode)
        guard = receipt["guards"][0]
        self.assertEqual("error", guard["outcome"])
        self.assertEqual(1, len(guard["assertionFailures"]))
        self.assertEqual(1, len(guard["testErrors"]))

    def test_timeout_retains_partial_channels_and_receipt_and_exits_one(self):
        process, receipt, output = self.run_control(
            "print('partial stdout', flush=True)\n"
            "print('partial stderr', file=sys.stderr, flush=True)\n"
            "time.sleep(5)"
        )
        self.assertEqual(1, process.returncode)
        guard = receipt["guards"][0]
        self.assertEqual("error", guard["outcome"])
        self.assertTrue(guard["timedOut"])
        self.assertIsNone(guard["returncode"])
        self.assertEqual(b"partial stdout\n", (output / guard["stdout"]).read_bytes())
        self.assertIn(b"partial stderr\n", (output / guard["stderr"]).read_bytes())

    def test_baseline_timeout_also_produces_receipt_and_exit_one(self):
        process, receipt, _ = self.run_control("return", baseline_action="time.sleep(5)")
        self.assertEqual(1, process.returncode)
        self.assertFalse(receipt["baselinePassed"])
        self.assertTrue(receipt["baseline"]["timedOut"])
        self.assertEqual([], receipt["guards"])

    def test_live_input_edits_cannot_change_snapshot_hash_or_mutation(self):
        process, receipt, _ = self.run_control(
            "self.fail('guard removed')",
            baseline_action=f"Path({str(self.verifier)!r}).write_text('# changed live input\\n')",
        )
        self.assertEqual(0, process.returncode)
        self.assertNotEqual(self.original_hash, hashlib.sha256(self.verifier.read_bytes()).hexdigest())
        self.assertEqual(self.original_hash, receipt["inputs"][(EVIDENCE / 'verify_class_map.py').as_posix()])
        self.assertEqual("require(False, 'blocked')", receipt["guards"][0]["guard"])
        self.assertEqual("killed", receipt["guards"][0]["outcome"])


if __name__ == "__main__":
    unittest.main()
