// Module-owned semantic-release hook; all publication gates stay in their existing hooks.
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { generateNotes as conventionalNotes } from '@semantic-release/release-notes-generator';

export async function generateNotes(pluginConfig, context) {
    const path = resolve(context.cwd, 'docs/release/migration-status.md');
    const status = await readFile(path, 'utf8');
    if (!status.trim()) throw new Error('Committed migration status must not be empty');
    const notes = await conventionalNotes(pluginConfig, context);
    return `${notes.trimEnd()}\n\n${status.trim()}\n`;
}
