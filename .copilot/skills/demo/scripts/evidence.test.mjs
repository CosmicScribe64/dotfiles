import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { runCommand } from './command.mjs';
import { confinedFile, loadArtifact, redactText, redactValue, storeArtifact } from './evidence.mjs';

async function temporaryDirectory(context) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'demonstration-test-'));
  context.after(() => rm(directory, { recursive: true, force: true }));
  return directory;
}

test('redacts literal secrets, credentials, ANSI escapes, and structured secret fields', () => {
  const text = redactText('api_key=hidden Authorization: Bearer abc123 postgres://name:pass@localhost/db \x1b[31mprivate-value', ['private-value']);
  for (const secret of ['hidden', 'abc123', 'name:pass', 'private-value', '\x1b']) assert.ok(!text.includes(secret));
  assert.deepEqual(redactValue({ rows: [{ access_token: 'hidden', state: 'ready' }], password: 'hidden' }), {
    rows: [{ access_token: '[REDACTED]', state: 'ready' }], password: '[REDACTED]',
  });
  assert.deepEqual(redactValue({ 'pa\x1b[31mssword\x1b[0m': 'hidden' }), { password: '[REDACTED]' });
});

test('normalizes terminal formatting before writing redacted evidence', async (context) => {
  const root = await temporaryDirectory(context);
  const secret = 'synthetic-private-46783';
  const inputs = [
    'synthetic-\x1b[31mprivate-46783\x1b[0m',
    '\x1b[31mapi_key\x1b[0m=assignment-secret',
    'api_\x1b[31mkey\x1b[0m="quoted secret"',
    'url=https://localhost/?access_token=query-secret',
    'postgres://fixture:user:password@localhost/db',
  ];
  const artifact = await storeArtifact(root, 'colored-log', 'text', inputs.join('\n'), [secret]);
  const saved = (await loadArtifact(root, artifact)).toString('utf8');
  for (const value of [secret, 'assignment-secret', 'quoted secret', 'query-secret', 'fixture:user:password', '\x1b']) {
    assert.ok(!saved.includes(value));
  }
  assert.match(saved, /api_key=\[REDACTED\]/);
  assert.equal(redactText('result=ready ordinary-key: unchanged'), 'result=ready ordinary-key: unchanged');
});

test('redacts long output within a bounded subprocess', async () => {
  const script = `
    import assert from 'node:assert/strict';
    import { redactText } from ${JSON.stringify(new URL('./evidence.mjs', import.meta.url).href)};
    for (const value of ['x'.repeat(2097152), 'token'.repeat(400000), 'https://' + 'name:'.repeat(400000)]) {
      assert.equal(redactText(value), value);
    }
    const key = 'token'.repeat(20000);
    assert.equal(redactText(key + '=private'), key + '=[REDACTED]');
    console.log('bounded-redaction:passed');
  `;
  const result = await runCommand([process.execPath, '--input-type=module', '-e', script], { timeoutMs: 5000, maxBytes: 4096 });
  assert.equal(result.timedOut, false, 'Redaction exceeded the watchdog');
  assert.equal(result.exitCode, 0, result.stderr);
  assert.equal(result.stdout.trim(), 'bounded-redaction:passed');
});

test('redacts before writing and verifies exact artifact bytes', async (context) => {
  const root = await temporaryDirectory(context);
  const artifact = await storeArtifact(root, 'build-stdout', 'text', 'result=ok secret=hidden');
  assert.ok(Number.isFinite(Date.parse(artifact.savedAt)));
  const bytes = await loadArtifact(root, artifact);
  assert.equal(bytes.toString(), 'result=ok secret=[REDACTED]');
  assert.equal((await readFile(path.join(root, artifact.file))).includes('hidden'), false);
  await writeFile(path.join(root, artifact.file), 'tampered');
  await assert.rejects(loadArtifact(root, artifact), /integrity/);
});

test('JSON stays parseable after nested redaction', async (context) => {
  const root = await temporaryDirectory(context);
  const artifact = await storeArtifact(root, 'rows', 'json', '{"count":2,"password":"hidden"}');
  assert.deepEqual(JSON.parse(await loadArtifact(root, artifact)), { count: 2, password: '[REDACTED]' });
});

test('rejects traversal, absolute paths, and symlink evidence', async (context) => {
  const root = await temporaryDirectory(context);
  for (const file of ['../outside', '/etc/passwd', 'artifacts/../../outside', 'artifacts\\outside', './file']) {
    await assert.rejects(confinedFile(root, file), /relative file path/);
  }
  await symlink('/etc/passwd', path.join(root, 'linked'));
  await assert.rejects(confinedFile(root, 'linked'), /Symlink/);
  await symlink(os.tmpdir(), path.join(root, 'artifacts'));
  await assert.rejects(storeArtifact(root, 'log', 'text', 'hello'), /Symlink/);
});

test('does not overwrite evidence or accept executable images', async (context) => {
  const root = await temporaryDirectory(context);
  await storeArtifact(root, 'log', 'text', 'original');
  await assert.rejects(storeArtifact(root, 'log', 'text', 'replacement'), /EEXIST/);
  await assert.rejects(storeArtifact(root, '../log', 'text', 'bad'), /Invalid/);
  await assert.rejects(storeArtifact(root, 'image', 'image', Buffer.from('<svg onload="alert(1)"/>')), /PNG/);
  await assert.rejects(storeArtifact(root, 'clip', 'video', Buffer.from('<script>')), /WebM/);
});
