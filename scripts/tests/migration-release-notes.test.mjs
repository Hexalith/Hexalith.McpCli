import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { generateNotes as conventionalNotes } from '@semantic-release/release-notes-generator';
import { generateNotes } from '../migration-release-notes.mjs';

const root = new URL('../../', import.meta.url);
const config = JSON.parse(await readFile(new URL('.releaserc.json', root), 'utf8'));
const status = await readFile(new URL('docs/release/migration-status.md', root), 'utf8');
const context = cwd => ({
    cwd, commits: [{ message: 'fix: preserve migration release status', hash: 'a'.repeat(40) }],
    lastRelease: { version: '2.0.1', gitTag: 'v2.0.1', gitHead: 'b'.repeat(40) },
    nextRelease: { version: '2.0.2', gitTag: 'v2.0.2', gitHead: 'a'.repeat(40) },
    options: { repositoryUrl: 'https://github.com/Hexalith/Hexalith.McpCli.git' },
    logger: { log() {} },
});

test('configured hook preserves the pinned generator output and appends the committed status once', async () => {
    assert.equal(config.plugins[1], './scripts/migration-release-notes.mjs');
    const temporary = await mkdtemp(join(tmpdir(), 'migration-notes-'));
    try {
        await mkdir(join(temporary, 'docs/release'), { recursive: true });
        await writeFile(join(temporary, 'docs/release/migration-status.md'), status);
        const ctx = context(temporary);
        const conventional = await conventionalNotes({}, ctx);
        const actual = await generateNotes({}, ctx);
        assert.equal(actual, `${conventional.trimEnd()}\n\n${status.trim()}\n`);
        assert.match(conventional, /preserve migration release status/);
        // Keep the release preflight, preparation, publisher and GitHub settings intact.
        assert.deepEqual(config.plugins[2], ['@semantic-release/exec', {
            verifyReleaseCmd: 'bash scripts/release-preflight.sh ${nextRelease.version}',
            prepareCmd: 'bash scripts/release-prepare.sh ${nextRelease.version} --verify-source',
            publishCmd: 'bash scripts/release-publish.sh ${nextRelease.version}',
        }]);
        assert.equal(config.plugins[3][0], '@semantic-release/github');
        assert.equal(config.plugins[3][1].assets.length, 4);
    } finally { await rm(temporary, { recursive: true, force: true }); }
});

test('missing or empty committed status fails closed before notes generation', async () => {
    const temporary = await mkdtemp(join(tmpdir(), 'migration-notes-missing-'));
    try {
        await assert.rejects(generateNotes({}, context(temporary)), { code: 'ENOENT' });
        await mkdir(join(temporary, 'docs/release'), { recursive: true });
        await writeFile(join(temporary, 'docs/release/migration-status.md'), ' \n');
        await assert.rejects(generateNotes({}, context(temporary)), {
            message: 'Committed migration status must not be empty',
        });
    } finally { await rm(temporary, { recursive: true, force: true }); }
});
