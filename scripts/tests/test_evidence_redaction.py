"""Synthetic regressions shared by CI retention, publication and evidence scans."""

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_redaction import known_credentials, sanitized, sanitized_values, sanitized_xml


class EvidenceRedactionTests(unittest.TestCase):
    def test_opaque_bearer_direct_json_and_repeated_escapes(self):
        for separator in (' ', '\t', '\n', '\r\n'):
            original = 'retained Authorization: bEaReR' + separator + 'opaque+/_~.credential== retained'
            for depth in range(4):
                value = original
                for _ in range(depth):
                    value = json.dumps(value).replace('b', '\\u0062')
                with self.subTest(separator=repr(separator), depth=depth):
                    result = sanitized(value, environment={})
                    self.assertNotIn('credential', result)
                    for _ in range(depth):
                        result = json.loads(result)
                    self.assertEqual('retained Authorization: Bearer [REDACTED] retained', result)

    def test_complete_and_truncated_pem_keep_safe_json_structure(self):
        for kind in ('PRIVATE KEY', 'RSA PRIVATE KEY', 'EC PRIVATE KEY', 'OPENSSH PRIVATE KEY', 'ENCRYPTED PRIVATE KEY'):
            for closed in (True, False):
                original = 'retained before\n-----BEGIN ' + kind + '-----\nsynthetic-private-material \"quoted snippet\" tail-material'
                if closed:
                    original += '\n-----END ' + kind + '-----\nretained after'
                for depth in range(4):
                    value = original
                    for _ in range(depth):
                        value = json.dumps({'diagnostic': value, 'safe': 'retained sibling'})
                    with self.subTest(kind=kind, closed=closed, depth=depth):
                        result = sanitized(value, environment={})
                        self.assertNotIn('synthetic-private-material', result)
                        self.assertNotIn('tail-material', result)
                        self.assertIn('retained before', result)
                        self.assertEqual(result, sanitized(result, environment={}))
                        for _ in range(depth):
                            result = json.loads(result)
                            self.assertEqual('retained sibling', result['safe'])
                            result = result['diagnostic']
                        self.assertIn('[REDACTED PEM]', result)
                        if closed:
                            self.assertIn('retained after', result)

    def test_malformed_xml_private_elements_and_settings(self):
        samples = (
            '<root><PrivateKey>synthetic-private-material</PrivateKey><unfinished',
            '<root><PrivateKey kind="rsa">synthetic-private-material</PrivateKey><unfinished',
            '<root name="ordinary"><setting name="PrivateKey">synthetic-private-material</setting><unfinished',
            '<root><ns:PrivateKey>synthetic-private-material</ns:PrivateKey><unfinished',
            '<root><Authentication__SigningKey>synthetic-private-material',
            '<root><setting name="PrivateKey">synthetic-private-material</setting><unfinished',
            '<root><setting name="PrivateKey" value="synthetic-private-material"/><unfinished',
            '<root><setting key="Authentication:SigningKey" value="synthetic-private-material"/><unfinished',
            '<root><child ns:PrivateKey="synthetic-private-material"/><unfinished',
            '<root><PrivateKey><d>synthetic-private-material</d></PrivateKey><unfinished',
        )
        for sample in samples:
            with self.subTest(sample=sample):
                for function in (sanitized, sanitized_xml):
                    result = function(sample, environment={})
                    self.assertNotIn('synthetic-private-material', result)
                    self.assertIn('[REDACTED]', result)
                    self.assertEqual(result, function(result, environment={}))
                    for depth in (1, 2):
                        value = sample
                        for _ in range(depth):
                            value = json.dumps(value)
                        result = function(value, environment={})
                        for _ in range(depth):
                            result = json.loads(result)
                        self.assertNotIn('synthetic-private-material', result)

    def test_xml_entities_cannot_hide_bearer_or_known_credentials(self):
        for sample in ('<root><failure message="Bearer&#32;opaque-credential"/><unfinished',
                       '<root>Bearer&#32;opaque-credential<unfinished'):
            self.assertNotIn('opaque-credential', sanitized_xml(sample, environment={}))
        secret = 'opaque-"credential&value'
        with patch.dict(os.environ, {'TEST_SECRET_TOKEN': secret}):
            value = '<root><failure message="opaque-&quot;credential&amp;value"/><unfinished'
            self.assertNotIn('credential', sanitized_xml(value))
            self.assertEqual(value, sanitized_xml(value, environment={}))

    def test_safe_xml_and_preexisting_redactions_are_byte_identical(self):
        for value in ('<root>\r\n  <child x = \'ordinary &amp; useful\' />\r\n</root>\r\n',
                      '<root><PrivateKey>[REDACTED]</PrivateKey><unfinished',
                      '<root><PrivateKey>[REDACTED PEM]</PrivateKey></root>',
                      '<root><setting name="PrivateKey" value="[REDACTED JWT]" /></root>',
                      '<root><setting name="PrivateKey" value="[REDACTED]"/><unfinished',
                      '{"SigningKey":"\\u005bREDACTED]", "ordinary":"SigningKey is configured"}',
                      'safe text with "quotes", back\\slashes and new\nlines'):
            with self.subTest(value=value):
                self.assertEqual(value, sanitized_xml(value, environment={}))

    def test_duplicate_private_containers_and_truncated_values(self):
        values = ('{"PrivateKey":{"d":"synthetic-private-material"},"PrivateKey":"[REDACTED]","safe":1}',
                  '{"PrivateKey":["synthetic-private-material"],"safe":1}',
                  '{"\\u0050rivateKey":"synthetic-private-material')
        for value in values:
            with self.subTest(value=value):
                result = sanitized(value, environment={})
                self.assertNotIn('synthetic-private-material', result)
                self.assertEqual(result, sanitized(result, environment={}))
        self.assertEqual({'PrivateKey': '[REDACTED]'}, sanitized_values({'PrivateKey': {'d': 'synthetic-private-material'}}, environment={}))

    def test_marker_like_private_values_are_still_redacted(self):
        for value in ('[REDACTEDbutsecret', '[REDACTED]trailing-secret'):
            result = sanitized('PrivateKey=' + value, environment={})
            self.assertEqual('PrivateKey=[REDACTED]', result)
        for marker in ('[REDACTED]', '[REDACTED PEM]', '[REDACTED JWT]', '<redacted>'):
            self.assertEqual('PrivateKey=' + marker, sanitized('PrivateKey=' + marker, environment={}))

    def test_review_xml_and_quoted_argument_boundaries_remain_safe_at_every_json_depth(self):
        values = (
            'prefix "quoted" <root><PrivateKey kind="rsa">private-canary</PrivateKey><unfinished',
            '<root><setting name="PrivateKey" value="private-canary',
            '<root><setting name="safe" key="PrivateKey" value="private-canary"/><unfinished',
            '<root><setting key="safe" name="PrivateKey" value="private-canary"/><unfinished',
            '--PrivateKey="private-canary with spaces" retained suffix',
            "--PrivateKey='private-canary with spaces' retained suffix",
            '--PrivateKey="private-canary with spaces',
            "--PrivateKey='private-canary with spaces",
        )
        for original in values:
            for depth in range(4):
                value = original
                for _ in range(depth):
                    value = json.dumps({'diagnostic': value, 'safe': 'retained sibling'})
                for function in (sanitized, sanitized_xml):
                    with self.subTest(depth=depth, function=function.__name__, original=original):
                        result = function(value, environment={})
                        self.assertNotIn('private-canary', result)
                        self.assertEqual(result, function(result, environment={}))
                        for _ in range(depth):
                            result = json.loads(result)
                            self.assertEqual('retained sibling', result['safe'])
                            result = result['diagnostic']
                        self.assertIn('[REDACTED]', result)
                        if original.endswith('retained suffix'):
                            self.assertIn('retained suffix', result)

    def test_changed_xml_also_redacts_every_entity_encoded_environment_credential(self):
        environment = {'TEST_SECRET': 'opaque-"credential&value'}
        original = '<root><PrivateKey>private-canary</PrivateKey><failure message="opaque-&quot;credential&amp;value"/><unfinished'
        for function in (sanitized, sanitized_xml):
            result = function(original, environment=environment)
            self.assertNotIn('private-canary', result)
            self.assertNotIn('credential', result)
            self.assertEqual(result, function(result, environment=environment))

    def test_empty_private_xml_preserves_exact_bytes_and_safe_siblings(self):
        for private in ('<PrivateKey/>', '<PrivateKey />', '<PrivateKey></PrivateKey>',
                        '<PrivateKey>  </PrivateKey>', '<setting name="PrivateKey"/>',
                        '<setting name="PrivateKey"></setting>'):
            for ending in ('</root>', '<unfinished'):
                original = '<root>' + private + '<safe>keep this diagnostic</safe>' + ending
                for function in (sanitized, sanitized_xml):
                    self.assertEqual(original, function(original, environment={}))

    def test_known_credentials_cannot_erase_secret_syntax_before_redaction(self):
        for known in ('a', 'Bearer', 'PrivateKey'):
            environment = {'TEST_SECRET': known}
            for original in ('Bearer secretKeyZX', '--PrivateKey=secretKeyZX',
                             '--PrivateKey="secretKeyZX with spaces"'):
                for depth in range(4):
                    value = original
                    for _ in range(depth):
                        value = json.dumps({'out': value, 'ok': 'kept'})
                    result = sanitized(value, environment=environment)
                    self.assertNotIn('secretKeyZX', result)
                    self.assertEqual(result, sanitized(result, environment=environment))
                    for _ in range(depth):
                        result = json.loads(result)
                        self.assertEqual('kept', result['ok'])
                        result = result['out']

    def test_known_environment_secrets_and_explicit_environment_are_shared(self):
        environment = {'TEST_SECRET': 'opaque-environment-credential', 'GH_TOKEN': 'short', 'EVENTSTORE_TOKEN': 'abc123', 'ordinary': 'kept'}
        self.assertEqual({'opaque-environment-credential', 'short', 'abc123'}, known_credentials(environment))
        self.assertEqual('kept [REDACTED]', sanitized('kept abc123', environment=environment))
        self.assertEqual('kept <redacted> <redacted>', sanitized('kept opaque-environment-credential short', environment=environment, marker='<redacted>'))
        self.assertEqual('kept opaque-environment-credential', sanitized('kept opaque-environment-credential', environment={}))
        overlapping = {'EVENTSTORE_TOKEN': 'long-canary', 'TEST_SECRET': 'E'}
        result = sanitized('long-canary E', environment=overlapping)
        self.assertEqual('[REDACTED] [REDACTED]', result)
        self.assertEqual(result, sanitized(result, environment=overlapping))
