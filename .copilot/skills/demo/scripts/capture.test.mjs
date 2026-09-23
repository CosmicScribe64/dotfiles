import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { allowedUrl, captureStep, collectSecrets, pointerValue } from './capture.mjs';
import { runCommand } from './command.mjs';
import { loadArtifact } from './evidence.mjs';
import { parseJson, validate } from './validate.mjs';

const command = { id: 'check', kind: 'command', title: 'Check', rationale: 'Assert a known result', argv: ['node', '--version'] };
const plan = { version: 1, title: 'Fixture', workspace: '.', steps: [command] };

test('the worked-example plan validates without preprocessing', async () => {
  validate('plan', JSON.parse(await readFile(new URL('../examples/plan.json', import.meta.url), 'utf8')));
});

test('validates strict plan shapes, identifiers, and capture consent', () => {
  assert.equal(validate('plan', plan), plan);
  assert.throws(() => validate('plan', { ...plan, unknown: true }), /Invalid plan/);
  assert.throws(() => validate('plan', { ...plan, steps: [command, command] }), /Duplicate/);
  assert.throws(() => validate('plan', { ...plan, steps: [{ ...command, typo: true }] }), /Invalid plan/);
  assert.throws(() => validate('plan', { ...plan, steps: [{ ...command, select: ['/id'] }] }), /Invalid plan/);
  const ui = { id: 'ui', title: 'UI', rationale: 'Inspect state', kind: 'ui', url: 'http://localhost:4173', actions: [], video: true };
  assert.throws(() => validate('plan', { ...plan, steps: [ui] }), /Invalid plan/);
  validate('plan', { ...plan, steps: [{ ...ui, sanitized: true }] });
  assert.throws(() => validate('plan', { ...plan, steps: [{ ...ui, sanitized: true, actions: [{ op: 'fill', selector: 'input', valueEnv: 'SECRET' }] }] }), /environment-sourced/);
});

test('hook events can import evidence but cannot execute commands', () => {
  const event = { version: 1, tool: 'screenshot_page', occurredAt: new Date().toISOString(), step: { id: 'import', kind: 'artifact', title: 'Capture', rationale: 'External observation', file: 'capture.png', media: 'image', sanitized: true } };
  validate('hook', event);
  assert.throws(() => validate('hook', { ...event, step: command }), /Invalid hook/);
  assert.throws(() => validate('run', {}), /Invalid run/);
});

test('rejects invalid callouts and unsafe JSON integers', () => {
  assert.throws(() => validate('plan', { ...plan, steps: [{ ...command, callouts: [{ type: 'box', x: 0.9, y: 0, width: 0.2, height: 0.1, label: 'Outside' }] }] }), /bounds/);
  assert.throws(() => validate('plan', { ...plan, steps: [{ ...command, callouts: [{ type: 'lines', start: 5, end: 2, label: 'Backwards' }] }] }), /line range/);
  assert.throws(() => parseJson('{"id":9007199254740993}'), /Unsafe JSON/);
  assert.equal(parseJson('{"id":"9007199254740993"}').id, '9007199254740993');
});

test('captures stdout, stderr, exact exit codes, and literal arguments without a shell', async () => {
  const result = await runCommand([process.execPath, '-e', 'console.log(process.argv[1]); console.error("diagnostic"); process.exitCode = 7', '$(not-a-shell)']);
  assert.equal(result.stdout.trim(), '$(not-a-shell)');
  assert.equal(result.stderr.trim(), 'diagnostic');
  assert.equal(result.exitCode, 7);
  assert.equal(result.timedOut, false);
});

test('bounds hung commands, output size, and missing executables', async () => {
  const timed = await runCommand([process.execPath, '-e', 'setInterval(() => {}, 1000)'], { timeoutMs: 120 });
  assert.equal(timed.timedOut, true);
  assert.notEqual(timed.exitCode, 0);
  const large = await runCommand([process.execPath, '-e', 'process.stdout.write("x".repeat(8192))'], { maxBytes: 512 });
  assert.equal(large.truncated, true);
  assert.match(large.stdout, /discarded/);
  assert.ok(large.stdout.length < 100);
  const missing = await runCommand(['demonstration-nonexistent-executable']);
  assert.match(missing.error, /ENOENT/);
});

async function fixture(context) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'demonstration-capture-'));
  context.after(() => rm(root, { recursive: true, force: true }));
  return { root, workspace: root, secrets: ['private-value'] };
}

test('captures failing checks without losing redacted logs', async (context) => {
  const options = await fixture(context);
  const result = await captureStep({ ...command, argv: [process.execPath, '-e', 'console.log("private-value"); console.error("details"); process.exitCode=3'], stdoutIncludes: ['not present'] }, options);
  assert.equal(result.status, 'failed');
  assert.equal(result.checks.filter((check) => !check.passed).length, 2);
  assert.equal(result.artifacts.length, 2);
  for (const artifact of result.artifacts) assert.ok(!(await readFile(path.join(options.root, artifact.file), 'utf8')).includes('private-value'));
  assert.ok(!JSON.stringify(result).includes('private-value'));
});

test('retains malformed structured command output as redacted failure evidence', async (context) => {
  const options = await fixture(context);
  const result = await captureStep({ ...command, format: 'json', argv: [process.execPath, '-e', 'console.log("not JSON: private-value")'] }, options);
  assert.equal(result.status, 'failed');
  const invalid = result.artifacts.find((artifact) => artifact.label === 'Invalid JSON standard output');
  assert.equal(invalid.phase, 'failure');
  assert.equal(await readFile(path.join(options.root, invalid.file), 'utf8'), 'not JSON: [REDACTED]\n');
});

test('short secret values cannot corrupt artifact paths, types, or hashes', async (context) => {
  const options = await fixture(context);
  const result = await captureStep({ ...command, argv: [process.execPath, '-e', 'console.log("a")'] }, { ...options, secrets: ['a'] });
  assert.equal(result.id, 'check');
  assert.equal(result.status, 'passed');
  for (const artifact of result.artifacts) {
    assert.match(artifact.file, /^artifacts\/check-/);
    assert.match(artifact.sha256, /^[a-f0-9]{64}$/);
    await loadArtifact(options.root, artifact);
  }
});

test('snapshots selected JSON fields and preserves missing-versus-null checks', async (context) => {
  const options = await fixture(context);
  await writeFile(path.join(options.root, 'rows.json'), '{"count":2,"access_token":"hidden","nested":{"a/b":true}}');
  const result = await captureStep({ id: 'rows', kind: 'json', title: 'Rows', rationale: 'Check records', file: 'rows.json', select: ['/count', '/nested/a~1b'], jsonEquals: [{ pointer: '/count', equals: 2 }, { pointer: '/missing', equals: null }] }, options);
  assert.equal(result.status, 'failed');
  const saved = JSON.parse(await readFile(path.join(options.root, result.artifacts[0].file), 'utf8'));
  assert.deepEqual(saved, { '/count': 2, '/nested/a~1b': true });
  assert.throws(() => pointerValue({}, '/__proto__'), /Missing/);
});

test('captures real API responses, redacts auth, and does not follow redirects', async (context) => {
  const options = await fixture(context);
  let redirected = false;
  const server = http.createServer((request, response) => {
    if (request.url === '/html') { response.end('<h1>Error: private-value</h1>'); return; }
    if (request.url === '/redirect') { response.writeHead(302, { location: '/other' }); response.end('{"redirect":true}'); return; }
    if (request.url === '/other') redirected = true;
    response.setHeader('content-type', 'application/json');
    response.end(JSON.stringify({ authorized: request.headers.authorization === 'Bearer private-value', token: 'hidden', count: 2 }));
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  context.after(() => new Promise((resolve) => { server.closeAllConnections(); server.close(resolve); }));
  const url = `http://127.0.0.1:${server.address().port}`;
  const step = { id: 'api', title: 'API', rationale: 'Read server state', kind: 'api', url, headersEnv: { Authorization: 'DEMO_AUTH' }, jsonEquals: [{ pointer: '/authorized', equals: true }] };
  const env = { DEMO_AUTH: 'Bearer private-value' };
  const result = await captureStep(step, { ...options, env, secrets: [...options.secrets, ...collectSecrets({ steps: [step] }, env)] });
  assert.equal(result.status, 'passed');
  assert.equal(JSON.parse(await readFile(path.join(options.root, result.artifacts[0].file))).token, '[REDACTED]');
  const redirect = await captureStep({ ...step, id: 'redirect', url: `${url}/redirect`, headersEnv: {}, jsonEquals: [] }, options);
  assert.equal(redirect.status, 'failed');
  assert.equal(redirected, false);
  const invalid = await captureStep({ ...step, id: 'invalid', url: `${url}/html`, headersEnv: {}, jsonEquals: [] }, options);
  assert.equal(invalid.status, 'failed');
  const body = invalid.artifacts.find((artifact) => artifact.label === 'Non-JSON API response');
  assert.equal(await readFile(path.join(options.root, body.file), 'utf8'), '<h1>Error: [REDACTED]</h1>');
  assert.throws(() => allowedUrl('https://example.invalid'), /not approved/);
  assert.throws(() => allowedUrl('file:///etc/passwd'), /HTTP/);
  assert.throws(() => collectSecrets({ steps: [], secretEnv: ['MISSING'] }, {}), /empty/);
});

test('scoped Git capture includes tracked and untracked changes only', async (context) => {
  const options = await fixture(context);
  for (const argv of [ ['git', 'init', '-q'], ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'fixture'] ]) {
    assert.equal((await runCommand(argv, { cwd: options.workspace })).exitCode, 0);
  }
  await writeFile(path.join(options.workspace, 'feature.txt'), 'new feature\n');
  await writeFile(path.join(options.workspace, 'unrelated.txt'), 'must not appear\n');
  const result = await captureStep({ id: 'diff', kind: 'diff', title: 'Change', rationale: 'Inspect scoped changes', paths: ['feature.txt'] }, options);
  assert.equal(result.status, 'observed');
  const diff = await readFile(path.join(options.root, result.artifacts[0].file), 'utf8');
  assert.match(diff, /\+new feature/);
  assert.ok(!diff.includes('unrelated.txt'));
});
