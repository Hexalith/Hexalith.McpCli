"""Synthetic regressions shared by CI retention, publication and evidence scans."""

import cProfile
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_redaction import known_credentials, sanitized, sanitized_values, sanitized_xml


class EvidenceRedactionTests(unittest.TestCase):
    def test_malformed_quoted_diagnostics_redact_credentials_and_preserve_safe_text(self):
        cases = (
            ('raw\ttab eyJcanary.payload.signature', 'raw\ttab [REDACTED JWT]'),
            (r'C:\Users\temp\new.log Bearer synthetic-canary', r'C:\Users\temp\new.log Bearer [REDACTED]'),
            (r'C:\Users\log Bearer\u0020synthetic-canary', '[REDACTED]'),
            (r'C:\Users\log Bearer synthetic\u002dcanary', '[REDACTED]'),
            (r'C:\Users\log \ud800 Bearer synthetic-canary', r'C:\Users\log \ud800 Bearer [REDACTED]'),
            ('details\n-----BEGIN PRIVATE KEY-----\nsynthetic-canary', 'details\n[REDACTED PEM]'),
        )
        for original, expected in cases:
            with self.subTest(original=original):
                prefix, suffix = 'log ', ' "safe sibling"'
                source = prefix + '"' + original + '"' + suffix
                result = sanitized(source, environment={})
                self.assertEqual((prefix + '"' + expected + '"' + suffix).encode(), result.encode())
                self.assertEqual(result, sanitized(result, environment={}))
                wrapped = json.dumps({'message': source, 'count': 2})
                self.assertEqual({'message': result, 'count': 2}, json.loads(sanitized(wrapped, environment={})))

        safe = 'log "raw\ttab and invalid escape \\q" kept'
        self.assertEqual(safe, sanitized(safe, environment={}))

    def test_quoted_angle_brackets_before_raw_xml(self):
        prefix = '{"comparison":"a < b << c", "empty":""}\n' * 256
        self.assertEqual(prefix, sanitized(prefix, environment={}))
        fragment = '<setting name="PrivateKey">synthetic-canary</setting><safe/>'
        self.assertEqual(prefix + fragment.replace('synthetic-canary', '[REDACTED]'),
                         sanitized(prefix + fragment, environment={}))

    def test_angle_bracket_scan_work_scales_with_the_number_of_records(self):
        def call_count(records):
            text = '{"msg":"a < b"}\n' * records
            profile = cProfile.Profile()
            self.assertEqual(text, profile.runcall(sanitized, text, environment={}))
            return sum(entry.callcount for entry in profile.getstats())

        # Count calls instead of wall time so runner load does not affect the bound.
        self.assertLess(call_count(1024), 10 * call_count(128))

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

    def test_truncated_escaped_private_fragments_preserve_json_wrappers(self):
        for escapes in ('\\', '\\\\\\'):
            quote = escapes + '"'
            prefix = 'diagnostic {' + quote + 'PrivateKey' + quote + ':' + quote
            for suffix in ('', quote + '} retained suffix'):
                original = prefix + 'synthetic-secret' + suffix
                expected = prefix + '[REDACTED]' + suffix
                with self.subTest(escapes=escapes, suffix=suffix):
                    self.assertEqual(expected, sanitized(original, environment={}))
                    wrapped = json.dumps({'out': original, 'safe': 'retained'})
                    result = sanitized(wrapped, environment={})
                    self.assertEqual({'out': expected, 'safe': 'retained'}, json.loads(result))
                    self.assertEqual(result, sanitized(result, environment={}))

    def test_escaped_private_json_preserves_safe_fields_after_strings_and_containers(self):
        for private in ('"synthetic-secret\\\\"', '"first\\"synthetic-secret"', '{"d":["synthetic-secret","]"]}'):
            for layers in (1, 2):
                fragment = r'{"\u0050rivateKey":' + private + ',"safe":"kept"}'
                for _ in range(layers):
                    fragment = json.dumps(fragment)[1:-1]
                with self.subTest(private=private, layers=layers):
                    result = sanitized('log: ' + fragment, environment={}).removeprefix('log: ')
                    for _ in range(layers):
                        result = json.loads('"' + result + '"')
                    self.assertEqual({'PrivateKey': '[REDACTED]', 'safe': 'kept'}, json.loads(result))

    def test_malformed_xml_uses_decoded_selectors_and_quote_aware_tags(self):
        for opening, ending in (
            ('<setting name="Private&#75;ey">', '</setting>'),
            ("<setting other='safe > detail' ns:key='Priv&#97;teKey'>", '</setting>'),
            ('<PrivateKey label="safe > detail">', '</PrivateKey>'),
        ):
            original = '<root name="ordinary">' + opening + 'synthetic-secret' + ending + '<safe/> <unfinished'
            expected = original.replace('synthetic-secret', '[REDACTED]')
            with self.subTest(opening=opening):
                self.assertEqual(expected, sanitized_xml(original, environment={}))
                self.assertEqual(expected, sanitized_xml(expected, environment={}))

        for opaque in ('<![CDATA[</setting>]]>', '<!-- </setting> -->'):
            prefix = '<root><setting name="Private&#75;ey">'
            suffix = '</setting><safe>kept</safe><unfinished'
            original = prefix + opaque + 'synthetic-secret' + suffix
            self.assertEqual(prefix + '[REDACTED]' + suffix, sanitized_xml(original, environment={}))

        for selector, name in (('', 'PrivateKey'), (' name="Private&#75;ey"', 'value')):
            for quote in ('"', "'"):
                prefix = '<root><setting' + selector + ' safe="kept > detail" ' + name + ' = ' + quote
                for suffix in (quote + '/><safe>kept</safe><unfinished', ''):
                    original = prefix + 'first>synthetic-secret' + suffix
                    expected = prefix + '[REDACTED]' + suffix
                    with self.subTest(selector=selector, quote=quote, suffix=suffix):
                        self.assertEqual(expected, sanitized_xml(original, environment={}))
                        self.assertEqual(expected, sanitized_xml(expected, environment={}))

    def test_private_arguments_accept_whitespace_and_escaped_quotes(self):
        cases = (
            ('--Authentication:JwtBearer:SigningKey ', 'synthetic-secret', ' --other kept'),
            ('--PrivateKey = "', 'synthetic-secret', '" kept'),
            ('--SigningKey : ', 'synthetic-secret', ' kept'),
            ('--PrivateKey\t"', 'synthetic\\"-secret', '" kept'),
            ("--PrivateKey='", "synthetic\\'-secret", "' kept"),
            ('--PrivateKey="', 'synthetic\\"-secret', ''),
            ('--PrivateKey="', 'synthetic-secret\\\\', '" kept'),
            ('--PrivateKey ', r'synthetic\ secret', ' kept'),
            ('--PrivateKey ', 'synthetic" secret"suffix', ' kept'),
        )
        for prefix, value, suffix in cases:
            with self.subTest(prefix=prefix, suffix=suffix):
                original = prefix + value + suffix
                expected = prefix + '[REDACTED]' + suffix
                self.assertEqual(expected, sanitized(original, environment={}))
                self.assertEqual(expected, sanitized(expected, environment={}))
                wrapped = json.dumps({'out': original, 'safe': 'retained'})
                self.assertEqual({'out': expected, 'safe': 'retained'},
                                 json.loads(sanitized(wrapped, environment={})))
        ordinary = 'PrivateKey is configured and ordinary --OtherPrivateKeys stay visible'
        self.assertEqual(ordinary, sanitized(ordinary, environment={}))
        self.assertEqual('--PrivateKey "[REDACTED]" kept',
                         sanitized('''--PrivateKey "synthetic"' secret'suffix kept''', environment={}))
        self.assertEqual("'--PrivateKey=[REDACTED]' kept",
                         sanitized("'--PrivateKey=synthetic secret' kept", environment={}))

    def test_private_argument_match_does_not_cross_protected_json_strings(self):
        diagnostic = json.dumps({'out': "--PrivateKey='synthetic-secret"})
        trailing = ' --PrivateKey="second-secret" kept'
        result = sanitized(diagnostic + trailing, environment={})
        expected = json.dumps({'out': "--PrivateKey='[REDACTED]"}) + ' --PrivateKey="[REDACTED]" kept'
        self.assertEqual(expected, result)
        self.assertEqual(result, sanitized(result, environment={}))

    def test_adjacent_private_argv_values_are_redacted(self):
        argv = ['fixture', '--Auth:PrivateKey', 'synthetic-secret', '--SigningKey', 'second-secret', 'kept']
        expected = ['fixture', '--Auth:PrivateKey', '[REDACTED]', '--SigningKey', '[REDACTED]', 'kept']
        self.assertEqual(expected, sanitized_values(argv, environment={}))
        wrapped = json.dumps({'argv': argv, 'out': '--PrivateKey', 'safe': 'kept'})
        result = sanitized(wrapped, environment={})
        self.assertEqual({'argv': expected, 'out': '--PrivateKey', 'safe': 'kept'}, json.loads(result))
        self.assertEqual(result, sanitized(result, environment={}))
        for trailing in ('', '"'):
            truncated = '["--PrivateKey", "synthetic-secret' + trailing
            self.assertEqual('["--PrivateKey", "[REDACTED]"', sanitized(truncated, environment={}))

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
