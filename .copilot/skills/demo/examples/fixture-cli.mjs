import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { filterTasks } from './filter.mjs';

const database = new DatabaseSync(fileURLToPath(new URL('./fixture.db', import.meta.url)), { readOnly: true });
try {
  const rows = database.prepare('SELECT id, title, completed FROM tasks ORDER BY id LIMIT 20').all();
  if (process.argv[2] === '--rows') console.log(JSON.stringify(rows));
  else if (process.argv[2] === '--verify') {
    const tasks = rows.map((row) => ({ ...row, completed: Boolean(row.completed) }));
    assert.equal(filterTasks(tasks, 'all').length, 3);
    assert.deepEqual(filterTasks(tasks, 'open').map((task) => task.id), ['task-1', 'task-2']);
    assert.deepEqual(filterTasks(tasks, 'done').map((task) => task.id), ['task-3']);
    assert.deepEqual(filterTasks([], 'open'), []);
    assert.throws(() => filterTasks(tasks, 'invalid'), /Unknown task filter/);
    await mkdir(new URL('./build/', import.meta.url), { recursive: true });
    await writeFile(new URL('./build/verification.json', import.meta.url), `${JSON.stringify({ feature: 'task-filter', assertions: 5, passed: true }, null, 2)}\n`);
    console.log('PASS: all, open, done, empty, and invalid-filter assertions');
  } else throw new Error('Expected --verify or --rows');
} finally { database.close(); }
