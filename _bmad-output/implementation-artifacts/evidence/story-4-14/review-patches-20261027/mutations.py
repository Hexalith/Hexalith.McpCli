import contextlib, importlib.util, io, json, pathlib, shutil, tempfile, unittest
root = pathlib.Path('/home/administrator/projects/hexalith/mcpcli')
checks = [
('P2 receipt containment', 'ci.py', "if path.name != 'result.json' or path.parent.parent != (runtime / 'runs').resolve():", 'if False:', 'test_vector_nonacceptance_and_nonzero_exits_still_run_smoke'),
('P3 smoke ownership', 'ci.py', "        require_owned(runs[0] / 'result.json', runtime)", '        pass', 'test_smoke_cleanup_proof_is_required_after_all_vectors_pass'),
('P4 runtime count', 'ci.py', "if len(list((runtime / 'runs').iterdir())) != 22:", 'if False:', 'test_extra_runtime_refuses_complete_lane_acceptance'),
('P5 generation redaction', 'ci.py', "for pattern in ('*.stdout.txt', '*.stderr.txt', 'tests.xml'):", 'for pattern in ():', 'test_generation_child_logs_and_xml_are_redacted'),
('P5 XML redaction', 'ci.py', "for pattern in ('*.stdout.txt', '*.stderr.txt', 'tests.xml'):", "for pattern in ('*.stdout.txt', '*.stderr.txt'):", 'test_generation_child_logs_and_xml_are_redacted'),
('P6 symlink path', 'ci.py', "if any(item.is_symlink() for item in [path, *path.parents] if ROOT in item.parents):", 'if False:', 'test_symlinked_evidence_is_refused_without_touching_its_target'),
('P7 preparation path', 'ci.py', "if source.resolve() != (evidence / 'preparation.json').resolve():", 'if False:', 'test_preparation_path_and_ownership_must_match_current_evidence'),
('P7 ownership ID', 'ci.py', "or prepared.get('ownershipId') != (evidence / OWNER_FILE).read_text().strip():", 'or False:', 'test_preparation_path_and_ownership_must_match_current_evidence'),
('P7 Integration DLL', 'ci.py', "or not TESTS.is_file():", ':', 'test_missing_built_integration_tests_refuses_live'),
('P7 Aspire version', 'ci.py', "if tools['aspire'].split('+')[0] != '13.6.1':", 'if False:', 'test_wrong_aspire_version_refuses_source_builds'),
('P7 preparation binary hash', 'ci.py', "if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:", 'if False:', 'test_bootstrapped_binary_hash_mismatch_refuses_preparation'),
('P7 preparation outer timeout', 'prepare-ci.sh', 'exec timeout --signal=TERM --kill-after=30s 2280 python3', 'exec python3', 'test_preparation_order_bounds_source_flags_and_nonsecret_exports'),
('P7 runner outer timeout', 'run-ci.sh', 'exec timeout --signal=TERM --kill-after=30s 17700 python3', 'exec python3', 'test_complete_lane_and_smoke_acceptance_retains_only_sanitized_diagnostics'),
('P7 Aspire install', 'ci.py', "if not shutil.which('aspire'):", 'if False:', 'test_missing_aspire_installs_only_a_digest_verified_release_archive'),
('D2 archive hash', 'ci.py', 'if digest != ASPIRE_CLI_SHA256:', 'if False:', 'test_missing_aspire_installs_only_a_digest_verified_release_archive'),
('P9 OpenSSL exact sonames', 'ci.py', 'ctypes.CDLL(library)', 'pass', 'test_exact_openssl_three_sonames_are_required_before_builds'),
('P11 cleanup grace', 'ci.py', 'child.wait(timeout=10)', 'child.wait(timeout=30)', 'test_cancellation_escalation_finishes_within_outer_kill_grace'),
('P12 reused runtime diagnostics', 'ci.py', "        if (prepared_runtime / 'runs').exists():", "        runtime = prepared_runtime\n        if (prepared_runtime / 'runs').exists():", 'test_missing_preparation_and_reused_runtime_refuse_live'),
]
results = []
for label, name, original, changed, method in checks:
    with tempfile.TemporaryDirectory(prefix='mcpcli-414-mutation-') as temporary:
        workspace = pathlib.Path(temporary)
        here = workspace / 'tools/live-topology'
        here.mkdir(parents=True)
        for file in ('ci.py', 'prepare-ci.sh', 'run-ci.sh', 'test_ci.py'):
            shutil.copyfile(root / 'tools/live-topology' / file, here / file)
        target = here / name
        content = target.read_text()
        assert content.count(original) == 1, (label, content.count(original))
        target.write_text(content.replace(original, changed))
        spec = importlib.util.spec_from_file_location('mutation_test', here / 'test_ci.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(module.CiHooksTests(method))
        caught = bool(result.failures) and not result.errors
        results.append({'guard': label, 'test': method, 'caughtByAssertion': caught, 'output': stream.getvalue()})
        print(label + ': ' + ('caught' if caught else 'NOT CAUGHT'), flush=True)
output = root / '_bmad-output/implementation-artifacts/evidence/story-4-14/review-patches-20261027/mutations.json'
output.write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(0 if all(row['caughtByAssertion'] for row in results) else 1)
