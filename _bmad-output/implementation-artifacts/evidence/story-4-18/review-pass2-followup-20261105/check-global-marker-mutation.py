"""Run only against unittest-owned fixture copies; never alter the repository scripts."""

import io
import json
import unittest
from unittest.mock import patch

import test_bootstrap_release as shell
import test_paired_publication as publication

original = shell.BootstrapReleaseTests.setUp


def setup(case):
    original(case)
    source = case.root / 'scripts/publish-paired-release.py'
    text = source.read_text()
    begin = text.index('    if not global_refs:\n')
    end = text.index("    subprocess.run(['gh', 'api', '--method', 'POST'", begin + len('    if not global_refs:\n'))
    end = text.index("    subprocess.run(['gh', 'api', '--method', 'POST'", end + 1)
    source.write_text(text[:begin] + text[end:])


with patch.object(shell.BootstrapReleaseTests, 'setUp', setup):
    result = unittest.TextTestRunner(stream=io.StringIO()).run(publication.PublicationTests(
        'test_configured_shell_hooks_publish_pair_and_first_source_bound_markers'))
assert not result.wasSuccessful() and len(result.failures) == 1 and not result.errors
print(json.dumps({'mutation': 'first-global-marker-creation-removed', 'detected': True,
                  'failures': len(result.failures), 'errors': len(result.errors)}))
