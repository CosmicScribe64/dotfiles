import assert from 'node:assert/strict';
import { cp, lstat, mkdir, mkdtemp, readFile, readlink, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { runCommand } from './command.mjs';
import { main } from './demo.mjs';
import { validate } from './validate.mjs';

test('all reusable templates satisfy their published input contracts', async () => {
  const load = async (name) => JSON.parse(await readFile(new URL(`../templates/${name}.json`, import.meta.url), 'utf8'));
  const plan = await load('plan');
  validate('plan', plan);
  validate('hook', await load('tool-event'));
  validate('plan', { ...plan, steps: [await load('database-step')] });
  assert.equal(await main(['validate', '--plan', fileURLToPath(new URL('../templates/plan.json', import.meta.url))]), 0);
  await assert.rejects(main(['run', '--plan', 'missing']), /Missing --out/);
  await assert.rejects(main(['build', '--run', '.', '--out', '.']), /does not apply/);
});

test('the real dotfiles installer includes the new skill in symlink and copy mode', async (context) => {
  const installer = new URL('../../../../setup.sh', import.meta.url);
  try { await lstat(installer); } catch (error) {
    if (error.code === 'ENOENT') { context.skip('Repository-only installer check; setup.sh is not part of a standalone skill install'); return; }
    throw error;
  }
  const root = await mkdtemp(path.join(os.tmpdir(), 'demonstration-install-'));
  context.after(() => rm(root, { recursive: true, force: true }));
  const repository = path.join(root, 'repo');
  const home = path.join(root, 'home');
  await mkdir(repository);
  await mkdir(home);
  const initialized = await runCommand(['git', 'init', '-q', repository], { cwd: root });
  assert.equal(initialized.exitCode, 0, initialized.stderr);
  await cp(installer, path.join(repository, 'setup.sh'));
  for (const file of ['.bashrc', '.tmux.conf', '.vimrc']) await writeFile(path.join(repository, file), 'fixture\n');
  await mkdir(path.join(repository, '.cows', 'custom-cows'), { recursive: true });
  const source = path.join(repository, '.copilot', 'skills', 'demo');
  await mkdir(source, { recursive: true });
  await cp(new URL('../', import.meta.url), source, { recursive: true, filter: (file) => path.basename(file) !== 'node_modules' });
  const target = path.join(home, '.copilot', 'skills', 'demo');
  const run = (options) => runCommand(['bash', path.join(repository, 'setup.sh'), '-y', ...options], { cwd: root, env: { ...process.env, HOME: home } });
  const linked = await run([]);
  assert.equal(linked.exitCode, 0, linked.stderr);
  assert.equal(await readlink(target), source);
  assert.equal((await run([])).exitCode, 0);
  const copied = await run(['--copy']);
  assert.equal(copied.exitCode, 0, copied.stderr);
  assert.equal((await lstat(target)).isSymbolicLink(), false);
  for (const file of ['SKILL.md', 'package-lock.json', 'schemas/plan.schema.json', 'scripts/demo.mjs', 'assets/deck.css', 'examples/app.html', 'templates/tool-event.json']) {
    assert.deepEqual(await readFile(path.join(target, file)), await readFile(path.join(source, file)));
  }
});
