import { lstat, readFile } from 'node:fs/promises';
import path from 'node:path';
import { isDeepStrictEqual } from 'node:util';
import { runCommand } from './command.mjs';
import { confinedFile, MAX_ARTIFACT_BYTES, redactText, redactValue, storeArtifact } from './evidence.mjs';
import { outcome, parseJson } from './validate.mjs';

export function allowedUrl(input, allowedOrigins = []) {
  const url = new URL(input);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
    throw new Error('Capture requires HTTP(S) without URL credentials');
  }
  if (!['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) && !allowedOrigins.includes(url.origin)) {
    throw new Error(`Origin is not approved: ${url.origin}`);
  }
  return url;
}

export function collectSecrets(plan, env = process.env) {
  const names = new Set(plan.secretEnv ?? []);
  for (const step of plan.steps) {
    for (const name of Object.values(step.headersEnv ?? {})) names.add(name);
    for (const action of step.actions ?? []) if (action.valueEnv) names.add(action.valueEnv);
  }
  return [...names].map((name) => {
    if (!env[name]) throw new Error(`Required environment variable is empty: ${name}`);
    return env[name];
  });
}

export function pointerValue(value, pointer) {
  let current = value;
  if (pointer === '') return current;
  for (const segment of pointer.slice(1).split('/')) {
    const key = segment.replaceAll('~1', '/').replaceAll('~0', '~');
    if (current === null || typeof current !== 'object' || !Object.hasOwn(current, key)) {
      throw new Error(`Missing JSON pointer: ${pointer}`);
    }
    current = current[key];
  }
  return current;
}

function checkJson(step, value, result, secrets) {
  for (const check of step.jsonEquals ?? []) {
    let actual;
    try { actual = pointerValue(value, check.pointer); } catch { actual = undefined; }
    result.checks.push({
      label: `JSON ${check.pointer || '/'} equals expected value`,
      expected: redactValue(check.equals, secrets, check.pointer),
      actual: redactValue(actual ?? null, secrets, check.pointer),
      passed: actual !== undefined && isDeepStrictEqual(actual, check.equals),
    });
  }
  return step.select ? Object.fromEntries(step.select.map((pointer) => [pointer, pointerValue(value, pointer)])) : value;
}

async function boundedFile(workspace, file) {
  const resolved = await confinedFile(workspace, file);
  if ((await lstat(resolved)).size > MAX_ARTIFACT_BYTES) throw new Error('Source file exceeds the byte limit');
  return readFile(resolved);
}

async function responseText(response) {
  if (!response.body) return '';
  const reader = response.body.getReader();
  const chunks = [];
  let length = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.length;
      if (length > 2097152) throw new Error('API response exceeds the byte limit');
      chunks.push(value);
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
  return Buffer.concat(chunks).toString('utf8');
}

async function scopedDiff(step, workspace) {
  for (const file of step.paths) {
    if (path.isAbsolute(file) || file.includes('\\') || file.includes('\0') || file.split('/').some((part) => !part || part === '..' || part === '.')) {
      throw new Error('Diff paths must be explicit workspace-relative files or directories');
    }
  }
  const deadline = performance.now() + (step.timeoutMs ?? 30000);
  const execute = async (argv, exits = [0]) => {
    const remaining = Math.floor(deadline - performance.now());
    if (remaining <= 0) throw new Error('Diff capture timed out');
    const result = await runCommand(argv, { cwd: workspace, timeoutMs: remaining });
    if (result.error || result.timedOut || result.truncated || !exits.includes(result.exitCode)) {
      throw new Error(`Git diff capture failed: ${result.error ?? result.stderr ?? result.exitCode}`);
    }
    return result.stdout;
  };
  let text = await execute(['git', '--literal-pathspecs', 'diff', '--no-ext-diff', '--no-textconv', '--no-color', step.base ?? 'HEAD', '--', ...step.paths]);
  const untracked = (await execute(['git', '--literal-pathspecs', 'ls-files', '--others', '--exclude-standard', '-z', '--', ...step.paths])).split('\0').filter(Boolean);
  if (untracked.length > 30) throw new Error('Diff capture is limited to 30 untracked files; narrow the paths');
  for (const file of untracked) {
    const resolved = await confinedFile(workspace, file);
    text += await execute(['git', 'diff', '--no-index', '--no-ext-diff', '--no-textconv', '--no-color', '--', '/dev/null', resolved], [0, 1]);
    if (Buffer.byteLength(text) > 2097152) throw new Error('Diff exceeds the byte limit; narrow the paths');
  }
  return text || '(No changes in the selected paths.)\n';
}

export async function captureStep(step, { root, workspace, allowedOrigins = [], secrets = [], env = process.env }) {
  const result = {
    id: step.id, title: step.title, rationale: step.rationale, edgeCases: step.edgeCases ?? [], kind: step.kind,
    startedAt: new Date().toISOString(), finishedAt: new Date().toISOString(), status: 'observed', source: {}, checks: [], artifacts: [],
  };
  const add = async (type, content, label, phase = 'output', callouts = step.callouts ?? []) => {
    const compatible = callouts.filter((callout) => callout.type === 'tag'
      || (callout.type === 'box' && type === 'image')
      || (callout.type === 'lines' && ['text', 'json', 'diff'].includes(type)));
    const artifact = await storeArtifact(root, `${step.id}-${String(result.artifacts.length + 1).padStart(2, '0')}`, type, content, secrets);
    result.artifacts.push({ ...artifact, label, phase, callouts: compatible });
  };
  try {
    if (step.kind === 'command') {
      const captured = await runCommand(step.argv, { cwd: workspace, env, timeoutMs: step.timeoutMs, maxBytes: step.maxBytes });
      const { stdout, stderr, ...metadata } = captured;
      result.source = { argv: step.argv, workingDirectory: workspace, ...metadata };
      result.checks.push({ label: 'Process exit code', expected: step.expectExit ?? 0, actual: captured.exitCode, passed: captured.exitCode === (step.expectExit ?? 0) });
      for (const stream of ['stdout', 'stderr']) {
        for (const fragment of step[`${stream}Includes`] ?? []) {
          result.checks.push({ label: `${stream} contains expected text`, expected: fragment, actual: captured[stream].includes(fragment), passed: captured[stream].includes(fragment) });
        }
      }
      await add('text', stderr, 'Standard error', 'output', (step.callouts ?? []).filter((callout) => callout.type === 'tag'));
      if (step.format === 'json' && !captured.truncated) {
        let parsed;
        try { parsed = parseJson(stdout); }
        catch (error) {
          await add('text', stdout, 'Invalid JSON standard output', 'failure', []);
          throw error;
        }
        const value = checkJson(step, parsed, result, secrets);
        await add('json', JSON.stringify(value), 'Structured command output');
      } else await add(step.format === 'diff' ? 'diff' : 'text', stdout, 'Standard output');
      if (captured.error || captured.timedOut || captured.truncated) {
        result.error = captured.error ?? (captured.timedOut ? 'Command timed out' : 'Command output exceeded the byte limit');
      }
    } else if (step.kind === 'api') {
      const url = allowedUrl(step.url, allowedOrigins);
      const headers = Object.fromEntries(Object.entries(step.headersEnv ?? {}).map(([header, name]) => [header, env[name]]));
      const response = await fetch(url, { method: 'GET', headers, redirect: 'manual', signal: AbortSignal.timeout(step.timeoutMs ?? 10000) });
      result.source = { method: 'GET', url: url.href, status: response.status, contentType: response.headers.get('content-type') };
      result.checks.push({ label: 'HTTP status', expected: step.expectStatus ?? 200, actual: response.status, passed: response.status === (step.expectStatus ?? 200) });
      const text = await responseText(response);
      let parsed;
      try { parsed = parseJson(text); }
      catch (error) {
        await add('text', text, 'Non-JSON API response', 'failure', []);
        throw error;
      }
      const value = checkJson(step, parsed, result, secrets);
      await add('json', JSON.stringify(value), 'API response');
    } else if (step.kind === 'json') {
      result.source = { file: step.file };
      const value = checkJson(step, parseJson((await boundedFile(workspace, step.file)).toString('utf8')), result, secrets);
      await add('json', JSON.stringify(value), 'JSON snapshot');
    } else if (step.kind === 'diff') {
      result.source = { base: step.base ?? 'HEAD', paths: step.paths, includesUntracked: true };
      await add('diff', await scopedDiff(step, workspace), 'Scoped code diff');
    } else if (step.kind === 'artifact') {
      result.source = { file: step.file, sanitized: step.sanitized ?? false };
      const bytes = await boundedFile(workspace, step.file);
      const content = ['image', 'video'].includes(step.media) ? bytes : bytes.toString('utf8');
      if (step.media === 'json') parseJson(content);
      await add(step.media, content, 'Imported evidence', 'imported');
    } else if (step.kind === 'ui') {
      const { captureUI } = await import('./ui.mjs');
      await captureUI(step, { result, add, allowedOrigins, env });
    } else throw new Error('Unsupported capture kind');
  } catch (error) {
    result.error = error.message;
  }
  if (result.error) await add('text', result.error, 'Capture failure', 'failure', []);
  result.status = outcome(result);
  result.finishedAt = new Date().toISOString();
  return {
    ...result,
    title: redactText(result.title, secrets), rationale: redactText(result.rationale, secrets),
    edgeCases: result.edgeCases.map((note) => redactText(note, secrets)),
    source: Object.fromEntries(Object.entries(result.source).map(([key, value]) => [key, redactValue(value, secrets)])),
    ...(result.error ? { error: redactText(result.error, secrets) } : {}),
    checks: result.checks.map((check) => ({
      ...check, label: redactText(check.label, secrets),
      ...(Object.hasOwn(check, 'expected') ? { expected: redactValue(check.expected, secrets) } : {}),
      ...(Object.hasOwn(check, 'actual') ? { actual: redactValue(check.actual, secrets) } : {}),
    })),
    artifacts: result.artifacts.map((artifact) => ({
      ...artifact, label: redactText(artifact.label, secrets),
      callouts: artifact.callouts.map((callout) => ({ ...callout, label: redactText(callout.label, secrets) })),
    })),
  };
}
