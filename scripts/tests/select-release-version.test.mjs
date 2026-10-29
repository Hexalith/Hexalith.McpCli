// Exercise the shipped selector with real Git/semantic-release; all fixture writes stay local.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { after, before, test } from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const temporary = mkdtempSync(join(tmpdir(), 'mcpcli-version-regression-'));
const evidence = process.env.MCPCLI_VERSION_TEST_EVIDENCE ?? mkdtempSync(join(tmpdir(), 'mcpcli-version-evidence-'));
mkdirSync(evidence, { recursive: true });
const selector = process.env.MCPCLI_VERSION_SELECTOR_SOURCE ?? join(root, 'scripts/select-release-version.mjs');
const seed = join(temporary, 'seed');
const env = { ...process.env, GIT_CONFIG_GLOBAL: join(temporary, 'empty.gitconfig'),
    GIT_CONFIG_SYSTEM: join(temporary, 'empty.gitconfig'), GIT_AUTHOR_DATE: '2001-01-01T00:00:00Z',
    GIT_COMMITTER_DATE: '2001-01-01T00:00:00Z' };
writeFileSync(env.GIT_CONFIG_GLOBAL, '');
for (const key of Object.keys(env)) {
    if (/^(GITHUB_|GH_|NUGET_)/.test(key)) delete env[key];
}
const commits = {};
const messages = {
    baseline: 'chore: seed the release version fixture\n',
    selected: 'fix: select the dispatched source\n',
    unrelated: 'feat: keep unrelated main history outside selection\n',
};

function retain(name, value) {
    writeFileSync(join(evidence, name), value, { flag: 'wx' });
}

function execute(argv, cwd, extra = {}) {
    const result = spawnSync(argv[0], argv.slice(1), { cwd, env, encoding: 'utf8', ...extra });
    assert.ifError(result.error);
    assert.equal(result.status, 0, `${argv.join(' ')}\n${result.stdout}\n${result.stderr}`);
    return result.stdout.trim();
}

function git(cwd, ...args) {
    return execute(['git', ...args], cwd);
}

function snapshot(cwd) {
    return {
        head: git(cwd, 'rev-parse', 'HEAD'),
        headFile: readFileSync(join(cwd, '.git/HEAD'), 'utf8'),
        refs: git(cwd, 'for-each-ref', '--format=%(refname) %(objectname) %(symref)'),
        status: git(cwd, 'status', '--porcelain', '--untracked-files=all'),
    };
}

before(() => {
    const pinned = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')).devDependencies;
    const installed = JSON.parse(readFileSync(join(root, 'node_modules/@commitlint/cli/package.json'), 'utf8'));
    assert.equal(installed.version, pinned['@commitlint/cli'], 'Run npm ci for the pinned commit validator.');
    mkdirSync(seed);
    git(seed, 'init', '--initial-branch=main');
    git(seed, 'config', 'user.name', 'Release Version Fixture');
    git(seed, 'config', 'user.email', 'release-version-fixture@example.invalid');
    mkdirSync(join(seed, 'scripts'));
    copyFileSync(selector, join(seed, 'scripts/select-release-version.mjs'));
    for (const name of ['package.json', '.releaserc.json', 'commitlint.config.mjs']) {
        copyFileSync(join(root, name), join(seed, name));
    }
    writeFileSync(join(seed, '.gitignore'), 'node_modules\n');
    symlinkSync(join(root, 'node_modules'), join(seed, 'node_modules'), 'junction');
    for (const [name, message] of Object.entries(messages)) {
        // Validate the exact complete candidate with the owning fixture's copied policy before using it.
        const argv = [process.execPath, join(root, 'node_modules/@commitlint/cli/cli.js'), '--verbose'];
        const validation = spawnSync(argv[0], argv.slice(1), { cwd: seed, env, input: message, encoding: 'utf8' });
        retain(`${name}.message.txt`, message);
        retain(`${name}.commitlint.stdout.txt`, validation.stdout ?? '');
        retain(`${name}.commitlint.stderr.txt`, validation.stderr ?? '');
        retain(`${name}.commitlint.command.json`, JSON.stringify({ argv, exit_code: validation.status }, null, 2) + '\n');
        assert.ifError(validation.error);
        assert.equal(validation.status, 0, validation.stdout + validation.stderr);
        const messagePath = join(temporary, `${name}.message.txt`);
        writeFileSync(messagePath, message);
        writeFileSync(join(seed, 'fixture.txt'), name + '\n');
        git(seed, 'add', '--all');
        git(seed, 'commit', '--file', messagePath);
        commits[name] = git(seed, 'rev-parse', 'HEAD');
        assert.match(commits[name], /^[0-9a-f]{40}$/);
        if (name === 'baseline') git(seed, 'tag', 'v1.0.0', commits[name]);
    }
    retain('fixture-commits.json', JSON.stringify(commits, null, 2) + '\n');
});

after(() => rmSync(temporary, { recursive: true, force: true }));

for (const scenario of ['absent-main', 'main-before-source', 'main-after-source']) {
    test(`detached source selects its exact patch release with ${scenario}`, () => {
        const source = join(temporary, scenario);
        git(temporary, 'clone', '--no-hardlinks', seed, source);
        // The symlink is ignored by Git and must be supplied explicitly to this fixture clone.
        symlinkSync(join(root, 'node_modules'), join(source, 'node_modules'), 'junction');
        git(source, 'checkout', '--detach', commits.selected);
        if (scenario === 'absent-main') git(source, 'update-ref', '-d', 'refs/heads/main');
        else git(source, 'update-ref', 'refs/heads/main', scenario === 'main-before-source' ? commits.baseline : commits.unrelated);
        assert.equal(git(source, 'branch', '--show-current'), '');
        const before = snapshot(source);
        const original = snapshot(root);
        const resultPath = join(temporary, `${scenario}.selection.json`);
        const argv = [process.execPath, join(source, 'scripts/select-release-version.mjs'), resultPath];
        const result = spawnSync(argv[0], argv.slice(1), { cwd: source, env, encoding: 'utf8' });
        const after = snapshot(source);
        retain(`${scenario}.stdout.txt`, result.stdout ?? '');
        retain(`${scenario}.stderr.txt`, result.stderr ?? '');
        retain(`${scenario}.result.json`, JSON.stringify({ argv, exit_code: result.status, commits,
            before, after, original_refs_unchanged: JSON.stringify(original) === JSON.stringify(snapshot(root)) }, null, 2) + '\n');
        assert.deepEqual(after, before, 'The original detached source refs, tags, HEAD and worktree must stay unchanged.');
        assert.deepEqual(snapshot(root), original, 'The owning repository must stay unchanged.');
        assert.ifError(result.error);
        assert.equal(result.status, 0, result.stdout + result.stderr);
        const receipt = JSON.parse(readFileSync(resultPath, 'utf8'));
        retain(`${scenario}.selection.json`, JSON.stringify(receipt, null, 2) + '\n');
        assert.deepEqual(receipt, { schema: 'mcpcli-version-selection/v1', source_sha: commits.selected,
            release: true, version: '1.0.1' });
    });
}
