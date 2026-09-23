import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { parseArgs } from 'node:util';
import { runCommand } from '../scripts/command.mjs';
import { runPlan } from '../scripts/run.mjs';
import { seedTasks, startExample } from './server.mjs';

const { values } = parseArgs({ options: { out: { type: 'string' } }, strict: true });
if (!values.out) throw new Error('Missing --out: choose a new directory under the repository\'s ignored scratch/');
const output = path.resolve(values.out);
const workspace = await mkdtemp(path.join(os.tmpdir(), 'demonstration-example-'));
let server;
try {
  await writeFile(path.join(workspace, 'filter.mjs'), 'export function filterTasks(tasks, status) {\n  return tasks;\n}\n');
  for (const argv of [
    ['git', 'init', '-q'], ['git', 'add', '--', 'filter.mjs'],
    ['git', '-c', 'user.name=Demonstration fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Synthetic baseline'],
  ]) {
    const result = await runCommand(argv, { cwd: workspace });
    if (result.exitCode !== 0) throw new Error(`Fixture setup failed: ${result.stderr}`);
  }
  for (const file of ['filter.mjs', 'fixture-cli.mjs']) await writeFile(path.join(workspace, file), await readFile(new URL(`./${file}`, import.meta.url)));
  const database = new DatabaseSync(path.join(workspace, 'fixture.db'));
  try {
    database.exec('CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, completed INTEGER NOT NULL)');
    const insert = database.prepare('INSERT INTO tasks (id, title, completed) VALUES (?, ?, ?)');
    for (const task of seedTasks) insert.run(task.id, task.title, Number(task.completed));
  } finally { database.close(); }
  server = await startExample();
  const plan = JSON.parse(await readFile(new URL('./plan.json', import.meta.url), 'utf8'));
  plan.workspace = workspace;
  for (const step of plan.steps) {
    if (step.url) step.url = new URL(new URL(step.url).pathname, server.url).href;
    if (step.kind === 'command') step.argv[0] = process.execPath;
  }
  const result = await runPlan(plan, { output, onStep: (step) => console.log(`${step.status.toUpperCase()}: ${step.id}`) });
  console.log(`Evidence preview: ${result.deck}\nManifest: ${path.join(result.root, 'run.json')}`);
  process.exitCode = result.run.steps.some((step) => step.status === 'failed') ? 1 : 0;
} finally {
  await server?.close();
  await rm(workspace, { recursive: true, force: true });
}
