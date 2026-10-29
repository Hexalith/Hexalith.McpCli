#!/usr/bin/env node
// All Git writes, including semantic-release's push-permission probe, target a temporary local remote.
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import semanticRelease from 'semantic-release';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
const output = process.argv[2];
if (!output || process.argv.length !== 3) throw new Error('Usage: select-release-version.mjs OUTPUT.json');
const temporary = mkdtempSync(join(tmpdir(), 'mcpcli-version-'));
const env = { ...process.env };
for (const key of Object.keys(env)) {
    if (/^(GITHUB_|GH_|GIT_|NUGET_)/.test(key) || ['CI', 'GITLAB_CI', 'JENKINS_URL'].includes(key)) delete env[key];
}
const gitConfig = join(temporary, 'empty.gitconfig');
writeFileSync(gitConfig, '');
env.GIT_CONFIG_GLOBAL = gitConfig;
env.GIT_CONFIG_SYSTEM = gitConfig;
const git = (...args) => execFileSync('git', args, { cwd: root, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
try {
    const installed = JSON.parse(readFileSync(join(dirname(require.resolve('semantic-release')), 'package.json'), 'utf8'));
    const pinned = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')).devDependencies['semantic-release'];
    if (installed.version !== pinned) throw new Error('Run npm ci to install the pinned semantic-release version.');
    const sha = git('rev-parse', 'HEAD');
    const remote = join(temporary, 'remote.git');
    const checkout = join(temporary, 'source');
    git('clone', '--mirror', '--no-hardlinks', root, remote);
    // Exact-SHA checkouts can have a detached HEAD and absent or unrelated local main.
    git('-C', remote, 'update-ref', 'refs/heads/main', sha);
    git('-C', remote, 'symbolic-ref', 'HEAD', 'refs/heads/main');
    git('clone', '--no-hardlinks', remote, checkout);
    git('-C', checkout, 'checkout', '-B', 'main', sha);
    const result = await semanticRelease({
        branches: ['main'], tagFormat: 'v${version}', repositoryUrl: remote,
        dryRun: true, ci: false,
        plugins: [require.resolve('@semantic-release/commit-analyzer')],
        extends: [],
    }, { cwd: checkout, env, stdout: process.stderr, stderr: process.stderr });
    const receipt = { schema: 'mcpcli-version-selection/v1', source_sha: sha,
        release: Boolean(result), version: result ? result.nextRelease.version : null };
    writeFileSync(output, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
    process.stdout.write(JSON.stringify(receipt) + '\n');
} finally {
    rmSync(temporary, { recursive: true, force: true });
}
