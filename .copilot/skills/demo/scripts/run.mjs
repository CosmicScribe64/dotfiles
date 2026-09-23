import { lstat, mkdir, open, readFile, realpath, rename, unlink } from 'node:fs/promises';
import path from 'node:path';
import { captureStep, collectSecrets } from './capture.mjs';
import { repositoryState } from './command.mjs';
import { confinedFile, redactText, sha256 } from './evidence.mjs';
import { renderDeck } from './render.mjs';
import { parseJson, validate } from './validate.mjs';

export async function readJsonFile(file, maxBytes = 1048576) {
  const stats = await lstat(file);
  if (!stats.isFile() || stats.size > maxBytes) throw new Error('JSON input must be a bounded regular file');
  return parseJson(await readFile(file, 'utf8'));
}

export async function withRunLock(root, action) {
  let lock;
  try { lock = await open(path.join(root, '.lock'), 'wx', 0o600); }
  catch (error) {
    if (error.code === 'EEXIST') throw new Error('Run is locked; check for an active writer before recovering a stale lock');
    throw error;
  }
  try { return await action(); }
  finally { await lock.close(); await unlink(path.join(root, '.lock')); }
}

async function persistRun(root, run) {
  validate('run', run);
  const temporary = path.join(root, 'run.json.next');
  const handle = await open(temporary, 'wx', 0o600);
  try {
    await handle.writeFile(`${JSON.stringify(run, null, 2)}\n`);
    await handle.close();
    await rename(temporary, path.join(root, 'run.json'));
  } finally {
    await handle.close();
    await unlink(temporary).catch((error) => { if (error.code !== 'ENOENT') throw error; });
  }
}

export async function loadRun(root) {
  return validate('run', await readJsonFile(await confinedFile(root, 'run.json'), 8388608));
}

export async function runPlan(plan, { output, baseDirectory = process.cwd(), env = process.env, onStep = () => {} }) {
  validate('plan', plan);
  for (const origin of plan.allowedOrigins ?? []) {
    const url = new URL(origin);
    if (!['http:', 'https:'].includes(url.protocol) || url.origin !== origin) throw new Error('allowedOrigins entries must be exact HTTP(S) origins');
  }
  const workspace = await realpath(path.resolve(baseDirectory, plan.workspace));
  if (!(await lstat(workspace)).isDirectory()) throw new Error('Workspace must be a directory');
  const secrets = collectSecrets(plan, env);
  const before = await repositoryState(workspace);
  const root = path.resolve(output);
  await mkdir(path.dirname(root), { recursive: true, mode: 0o700 });
  await mkdir(root, { mode: 0o700 });
  return withRunLock(root, async () => {
    const run = {
      version: 1, title: redactText(plan.title, secrets), state: 'running',
      startedAt: new Date().toISOString(), finishedAt: new Date().toISOString(),
      planSha256: sha256(JSON.stringify(plan)), repository: { before, after: before }, steps: [],
    };
    for (const step of plan.steps) {
      run.steps.push(await captureStep(step, { root, workspace, allowedOrigins: plan.allowedOrigins, secrets, env }));
      run.finishedAt = new Date().toISOString();
      run.repository.after = await repositoryState(workspace);
      await persistRun(root, run);
      onStep(run.steps.at(-1));
    }
    run.state = 'complete';
    run.finishedAt = new Date().toISOString();
    await persistRun(root, run);
    const deck = await renderDeck(root, run);
    return { root, run, deck };
  });
}

export async function appendEvent(event, { root, workspace, secretEnv = [], env = process.env }) {
  validate('hook', event);
  const secrets = collectSecrets({ steps: [], secretEnv }, env);
  const resolvedWorkspace = await realpath(workspace);
  return withRunLock(root, async () => {
    const run = await loadRun(root);
    if (run.steps.some((step) => step.id === event.step.id)) throw new Error('Duplicate step id');
    if (run.steps.length >= 100) throw new Error('Run step limit reached');
    const captured = await captureStep(event.step, { root, workspace: resolvedWorkspace, secrets, env });
    captured.source.tool = redactText(event.tool, secrets);
    captured.source.occurredAt = event.occurredAt;
    run.steps.push(captured);
    run.finishedAt = new Date().toISOString();
    await persistRun(root, run);
    const deck = await renderDeck(root, run);
    return { root, run, deck };
  });
}
