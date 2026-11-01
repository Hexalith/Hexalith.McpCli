"""Run in-memory negative controls; repository sources and Git remain untouched."""
import hashlib, io, json
from pathlib import Path
import sys, unittest
from unittest.mock import patch
root=Path('/home/administrator/projects/hexalith/mcpcli')
sys.path[:0]=[str(root/'scripts'),str(root/'scripts/tests')]
import paired_release
import test_paired_publication as tests
import test_paired_release as fixtures
original=paired_release.module
cases=[
 ('operator-decision','verify-paired-publication',"        operator_acceptance(operator_path, prepared, accepted_path, origin, actor)\n",'', 'PublicationTests.test_operator_decision_requires_fresh_complete_hash_bound_actual_sessions'),
 ('acceptance-source','verify-paired-publication',"        validate_source_evidence(read_json(acceptance_source), sha)\n",'', 'PublicationTests.test_acceptance_source_is_cross_checked_even_with_authentic_archive_digest'),
 ('original-archive-digest','verify-paired-publication'," or 'sha256:' + digest(archive) != artifact['digest']",'', 'PublicationTests.test_original_staging_archive_source_version_and_acceptance_source_must_match'),
 ('uncertain-push-stop','publish-paired-release','if pushed.returncode != 0:', 'if False:', 'PublicationTests.test_partial_uncertain_and_public_mismatch_outcomes_are_retained_without_retry'),
 ('public-content-match','publish-paired-release','if staged_contents != public_contents:', 'if False:', 'PublicationTests.test_partial_uncertain_and_public_mismatch_outcomes_are_retained_without_retry'),
 ('source-before-each-push','publish-paired-release',"                preflight(snapshot / 'candidate', snapshot / 'operator.json', version,\n                          OUTCOMES / f'before-push-{index + 1}.json')\n",'', 'PublicationTests.test_partial_uncertain_and_public_mismatch_outcomes_are_retained_without_retry'),
 ('both-feed-identities','release-request',"for identity in ('Hexalith.McpCli.Abstractions', 'Hexalith.McpCli'):","for identity in ('Hexalith.McpCli.Abstractions',):",'PublicationBoundaryTests.test_both_registry_identities_are_checked_and_occupied_version_fails'),
 ('bootstrap-line-marker','release-request','if marker != []:', 'if False:', 'PublicationBoundaryTests.test_global_marker_closes_new_bootstrap_and_second_paired_version_remains_possible'),
 ('uncertain-repeat-marker','publish-paired-release',"if gate.github_json(endpoint + version_marker) != []:", 'if False:', 'PublicationBoundaryTests.test_global_marker_closes_new_bootstrap_and_second_paired_version_remains_possible'),
 ('private-snapshot','publish-paired-release',"            shutil.copytree(IMPORTED, snapshot, symlinks=True)","            snapshot = IMPORTED",'PublicationTests.test_snapshot_survives_original_import_changes_and_pushes_only_checked_bytes'),
 ('staging-job-execution','verify-paired-publication',"    module('verify-release-source').verify_jobs(repository, run, STAGING_JOBS)\n",'', 'PublicationBoundaryTests.test_original_run_and_artifact_metadata_must_be_exact_and_jobs_executed'),
 ('operator-excerpt-hash','verify-paired-publication',"or hashlib.sha256(content.encode('utf-8')).hexdigest() != record.get('sha256')",'or False','PublicationTests.test_operator_decision_requires_fresh_complete_hash_bound_actual_sessions'),
 ('blocking-source-step','paired_release',"        verifier.validate_jobs(run.get('jobs', []), required)\n",'', 'PublicationTests.test_acceptance_source_is_cross_checked_even_with_authentic_archive_digest'),
 ('release-automation-gate','verify-release-source',"    'release-automation': ['Verify pinned release automation and refusal guards', 'Verify detached-source semantic-release version selection'],\n",'', 'PublicationBoundaryTests.test_full_ci_requires_the_release_automation_job_and_both_executed_steps'),
 ('confirmed-first-absence','release-request','if registration_error.code == 404:', 'if True:', 'PublicationBoundaryTests.test_first_ever_absence_requires_both_explicit_404s'),
 ('packed-readme-match','verify-paired-publication',"if archive.read('README.md') != (ROOT / 'README.md').read_bytes():",'if False:', 'PublicationTests.test_packed_readme_and_nuspec_are_rechecked_without_building'),
 ('downloaded-artifact-digest','verify-paired-publication',"if 'sha256:' + hashlib.sha256(response.stdout).hexdigest() != artifact['digest']:",'if False:', 'PublicationBoundaryTests.test_authenticated_fetch_checks_downloaded_bytes_and_preserves_prior_attempts'),
 ('credential-before-record','verify-paired-publication',"    require_sanitized_operator(decision)\n    write_new(output, decision)","    write_new(output, decision)",'PublicationBoundaryTests.test_operator_recording_refuses_known_credentials_and_retention_redacts_rejected_packets'),
 ('credential-before-import','publish-paired-release',"    module('verify-paired-publication').require_sanitized_operator(operator)\n",'', 'PublicationTests.test_credentials_are_refused_before_operator_packet_is_copied_into_import'),
 ('credential-retention-redaction','verify-paired-publication',"            retained = retained.replace(value, '[REDACTED]')","            retained = retained",'PublicationBoundaryTests.test_operator_recording_refuses_known_credentials_and_retention_redacts_rejected_packets'),

 ('bootstrap-historical-ancestry','release-request','if sha == first_pair or ancestor.returncode != 0:', 'if False:', 'PublicationBoundaryTests.test_bootstrap_recovery_cannot_target_paired_or_later_release_tags'),
 ('bootstrap-paired-version-refusal','release-request',"if not isinstance(version_markers, list) or any(item.get('ref') == version_ref for item in version_markers):",'if False:', 'PublicationBoundaryTests.test_bootstrap_recovery_cannot_target_paired_or_later_release_tags'),
 ('bootstrap-first-marker-state','release-request','if references == []:', 'if True:', 'PublicationBoundaryTests.test_bootstrap_recovery_cannot_target_paired_or_later_release_tags'),

 ('remaining-version-availability','publish-paired-release',"if version.lower() in {item.lower() for item in available}:",'if False:', 'PublicationTests.test_partial_uncertain_and_public_mismatch_outcomes_are_retained_without_retry'),

]
results=[]
for label,target,old,new,test in cases:
    path=root/'scripts'/(target+'.py')
    text=path.read_text();assert text.count(old)==1,(label,text.count(old))
    mutated=text.replace(old,new)
    def loader(name):
        loaded=original(name)
        if name==target:
            exec(compile(mutated,str(path),'exec'),loaded.__dict__)
        return loaded
    stream=io.StringIO()
    if target=='paired_release':
        namespace={};exec(compile(mutated,str(path),'exec'),dict(paired_release.__dict__),namespace)
        patch_context=patch.object(paired_release,'validate_source_evidence',namespace['validate_source_evidence'])
    else:
        patch_context=patch.object(paired_release,'module',loader)
    with patch_context,patch.object(tests,'module',loader),patch.object(fixtures,'module',loader):
        suite=unittest.defaultTestLoader.loadTestsFromName(test,tests)
        result=unittest.TextTestRunner(stream=stream,verbosity=0).run(suite)
    results.append({'guard':label,'source':str(path.relative_to(root)),'original_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'mutation':{'remove':old,'replace':new},'test':test,'tests_run':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'detected':not result.wasSuccessful(),'diagnostic':stream.getvalue()[-1800:]})
Path('/tmp/mcpcli-418-guard-mutations.json').write_text(json.dumps({'schema':'mcpcli-guard-removal-evidence/v1','mutations':results,
    'status':'passed' if all(item['detected'] for item in results) else 'failed','repository_files_changed':False},indent=2)+'\n')
print(sum(item['detected'] for item in results),'/',len(results),'guard removals detected')
if not all(item['detected'] for item in results):
    print([item['guard'] for item in results if not item['detected']]);sys.exit(1)
