### The paired semantic-release publish hook has no execution coverage

- Changed surface: `scripts/release-publish.sh:11` adds dispatch from the `paired` phase to the immutable pair publisher.
- Impacted consumer: semantic-release invokes this shell entry point through `.releaserc.json:14`.
- Existing test evidence: Regression gap. `scripts/tests/test_paired_publication.py:158` asserts exact pushed bytes and public outcomes, but invokes `self.publisher.publish(VERSION)` directly. The shell harness defaults to bootstrap at `scripts/tests/test_bootstrap_release.py:54`; its invalid-request matrix at line635 exercises unknown phases and invalid bootstrap versions. Searches for release-publish.sh and publish(VERSION) found no paired shell execution test.
- Missing verification: Execute the configured shell hooks with MCPCLI_RELEASE_PHASE=paired and synthetic accepted evidence, then assert both accepted archives are pushed and the complete public-pair outcome is produced.
- Demonstration: Changed the paired selector to broken-paired in each test-owned temporary copy of release-publish.sh. All141 normally discovered Python tests passed, zero failures/errors/skips. Python publisher assertions never execute the broken dispatch branch.
- Consequence: An accepted paired release can fail at its production publish hook while required release-automation remains green.
- Filed disposition: patch; add test_paired_shell_hooks_publish_the_preflighted_pair with synthetic subprocess/registry fixtures executing actual hooks.

Other finding: verify-paired-publication.py:238 still requires tenant_read.tenant == system, also prescribed by checklist:89. Tenants7.0.4 requires the selected canonical tenant (README:358). The fixture at test_paired_publication.py:90 hides drift by hardcoding system. Replacing only each fixture session read tenant with selected_tenant reproduces refusal: Client sessions must prove the approved command and matching persisted synthetic Party.
