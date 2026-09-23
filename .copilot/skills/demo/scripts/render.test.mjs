import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import test from 'node:test';
import { chromium } from 'playwright';
import { runCommand } from './command.mjs';
import { appendEvent, loadRun, runPlan, withRunLock } from './run.mjs';
import { renderDeck } from './render.mjs';
import { main } from './demo.mjs';

test('keeps sensitive JSON assertion values out of every persisted output', async (context) => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), 'demonstration-assertion-privacy-'));
  context.after(() => rm(workspace, { recursive: true, force: true }));
  const response = { token: 'synthetic-private-46783', credentials: { password: ['synthetic-nested-46783'] }, 'token/value': 'synthetic-escaped-46783', count: 2 };
  await writeFile(path.join(workspace, 'response.json'), JSON.stringify(response));
  const server = http.createServer((request, reply) => { reply.setHeader('content-type', 'application/json'); reply.end(JSON.stringify(response)); });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  context.after(() => new Promise((resolve) => { server.closeAllConnections(); server.close(resolve); }));
  const jsonEquals = [
    { pointer: '/token', equals: response.token },
    { pointer: '/token', equals: 'synthetic-unexpected-46783' },
    { pointer: '/credentials/password/0', equals: response.credentials.password[0] },
    { pointer: '/token~1value', equals: response['token/value'] },
    { pointer: '/count', equals: 2 },
    { pointer: '/missing', equals: null },
  ];
  const steps = [
    { id: 'file', kind: 'json', file: 'response.json' },
    { id: 'api', kind: 'api', url: `http://127.0.0.1:${server.address().port}` },
    { id: 'command', kind: 'command', format: 'json', argv: [process.execPath, '-e', 'process.stdout.write(require("node:fs").readFileSync("response.json"))'] },
  ].map((step) => ({ ...step, title: 'Sensitive JSON assertion', rationale: 'Compare original values without disclosing them', jsonEquals }));
  const { root, run, deck } = await runPlan({ version: 1, title: 'Assertion privacy', workspace, steps }, { output: path.join(workspace, 'run') });
  const persisted = [await readFile(path.join(root, 'run.json'), 'utf8'), await readFile(deck, 'utf8')];
  for (const step of run.steps) {
    assert.equal(step.status, 'failed');
    const checks = step.checks.slice(-jsonEquals.length);
    assert.deepEqual(checks.map((check) => check.passed), [true, false, true, true, true, false]);
    for (const check of checks.slice(0, 4)) {
      assert.equal(check.actual, '[REDACTED]');
      assert.equal(check.expected, '[REDACTED]');
    }
    assert.equal(checks[4].actual, 2);
    assert.equal(checks[4].expected, 2);
    for (const artifact of step.artifacts) persisted.push(await readFile(path.join(root, artifact.file), 'utf8'));
  }
  for (const content of persisted) {
    for (const secret of [response.token, response.credentials.password[0], response['token/value'], jsonEquals[1].equals]) {
      assert.ok(!content.includes(secret), 'Sensitive assertion data reached persisted output');
    }
  }
});

test('completes long-output capture and rendering within a subprocess watchdog', async (context) => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), 'demonstration-pipeline-budget-'));
  context.after(() => rm(workspace, { recursive: true, force: true }));
  const root = path.join(workspace, 'run');
  const plan = {
    version: 1, title: 'Bounded output', workspace,
    steps: [{ id: 'long-output', kind: 'command', title: 'Long log', rationale: 'Post-processing must complete after the command exits', argv: [process.execPath, '-e', 'process.stdout.write("x".repeat(524288))'], timeoutMs: 1000 }],
  };
  const script = `import { runPlan } from ${JSON.stringify(new URL('./run.mjs', import.meta.url).href)}; await runPlan(${JSON.stringify(plan)}, { output: ${JSON.stringify(root)} });`;
  const result = await runCommand([process.execPath, '--input-type=module', '-e', script], { timeoutMs: 5000, maxBytes: 4096 });
  assert.equal(result.timedOut, false, 'Capture or rendering exceeded the watchdog');
  assert.equal(result.exitCode, 0, result.stderr);
  const run = await loadRun(root);
  assert.equal(run.state, 'complete');
  assert.equal(run.steps[0].status, 'passed');
  const output = run.steps[0].artifacts.find((artifact) => artifact.label === 'Standard output');
  assert.equal(await readFile(path.join(root, output.file), 'utf8'), 'x'.repeat(524288));
  assert.match(await readFile(path.join(root, 'index.html'), 'utf8'), /<!doctype html>/);
});

test('prefers named UI states over duplicate frames and supporting command output', async (context) => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), 'demonstration-showcase-'));
  context.after(() => rm(workspace, { recursive: true, force: true }));
  const server = http.createServer((request, reply) => { reply.setHeader('content-type', 'text/html'); reply.end('<main><h1>Finished</h1></main>'); });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  context.after(() => new Promise((resolve) => { server.closeAllConnections(); server.close(resolve); }));
  const steps = [
    { id: 'ui', kind: 'ui', title: 'Show the result', rationale: 'Read the finished state', url: `http://127.0.0.1:${server.address().port}`, actions: [{ op: 'expectText', selector: 'h1', text: 'Finished' }, { op: 'snapshot', label: 'Finished screen' }] },
    { id: 'check', kind: 'command', title: 'Technical check', rationale: 'Keep the process output', argv: [process.execPath, '-e', 'console.log("PASS")'] },
  ];
  const { root, run, deck } = await runPlan({ version: 1, title: 'Feature demo', workspace, steps }, { output: path.join(workspace, 'run') });
  assert.deepEqual(run.steps.map((step) => step.status), ['passed', 'passed']);
  assert.equal(run.steps[0].artifacts.length, 4);
  const html = await readFile(deck, 'utf8');
  assert.match(html, /data-artifact="ui-02"/);
  assert.doesNotMatch(html, /data-artifact="ui-01"|data-artifact="ui-03"|data-step="check"/);
  assert.equal((html.match(/class="demo-slide"/g) ?? []).length, 1);
  assert.match(await readFile(path.join(root, run.steps[1].artifacts.find((artifact) => artifact.bytes).file), 'utf8'), /PASS/);
});

test('builds an offline, escaped deck with strict layout, checks, and line callouts', async (context) => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), 'demonstration-render-'));
  context.after(() => rm(workspace, { recursive: true, force: true }));
  const plan = {
    version: 1, title: '<script>window.injected=true</script>', workspace,
    steps: [{ id: 'assert', title: 'Assert output', kind: 'command', rationale: 'A literal string must not execute', argv: [process.execPath, '-e', 'console.log("<img src=x onerror=alert(1)>")'], stdoutIncludes: ['<img'], callouts: [{ type: 'lines', start: 1, end: 1, label: 'Literal output' }] }],
  };
  const { root, run, deck } = await runPlan(plan, { output: path.join(workspace, 'run') });
  assert.equal(run.state, 'complete');
  assert.equal(run.steps[0].status, 'passed');
  assert.deepEqual(run.steps[0].artifacts[0].callouts, []);
  assert.equal((await loadRun(root)).planSha256, run.planSha256);
  const html = await readFile(deck, 'utf8');
  assert.match(html, /&lt;script&gt;window.injected=true&lt;\/script&gt;/);
  assert.match(html, /Content-Security-Policy/);
  const empty = run.steps[0].artifacts.find((artifact) => artifact.bytes === 0);
  assert.ok(empty);
  assert.doesNotMatch(html, new RegExp(`data-artifact="${empty.id}"`));
  for (const block of ['title-block', 'evidence-deck', 'agent-commentary', 'highlighted']) assert.ok(html.includes(block));
  const browser = await chromium.launch({ headless: true });
  context.after(() => browser.close());
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.context().setOffline(true);
  await page.goto(pathToFileURL(deck).href);
  await page.waitForFunction(() => window.demonstrationDeck?.isReady());
  assert.equal(await page.evaluate(() => window.injected), undefined);
  await page.evaluate(() => window.demonstrationDeck.next());
  assert.equal(await page.locator('section.present .highlighted').count(), 1);
  for (const { viewport, colorScheme } of [
    { viewport: { width: 1440, height: 1000 }, colorScheme: 'light' },
    { viewport: { width: 1440, height: 1000 }, colorScheme: 'dark' },
    { viewport: { width: 390, height: 844 }, colorScheme: 'light' },
    { viewport: { width: 390, height: 844 }, colorScheme: 'dark' },
    { viewport: { width: 320, height: 640 }, colorScheme: 'dark' },
  ]) {
    await page.setViewportSize(viewport);
    await page.emulateMedia({ colorScheme });
    assert.equal(await page.evaluate(() => getComputedStyle(document.body).backgroundColor), colorScheme === 'dark' ? 'rgb(24, 27, 29)' : 'rgb(250, 252, 252)');
    const geometry = await page.locator('section.present').evaluate((slide) => {
      const title = slide.querySelector('.title-block').getBoundingClientRect();
      const evidence = slide.querySelector('.evidence-deck').getBoundingClientRect();
      const notes = slide.querySelector('.agent-commentary').getBoundingClientRect();
      const horizontalOverlap = Math.min(evidence.right, notes.right) - Math.max(evidence.left, notes.left);
      const verticalOverlap = Math.min(evidence.bottom, notes.bottom) - Math.max(evidence.top, notes.top);
      const navigation = document.querySelector('.controls').getBoundingClientRect();
      const theme = document.querySelector('.theme-controls').getBoundingClientRect();
      return { overflow: slide.scrollWidth > slide.clientWidth + 1, titleOverlaps: title.bottom > evidence.top, regionsOverlap: horizontalOverlap > 1 && verticalOverlap > 1, navigationOverlaps: slide.getBoundingClientRect().bottom > Math.min(navigation.top, theme.top) + 1, controlsOverlap: theme.right > navigation.left };
    });
    assert.deepEqual(geometry, { overflow: false, titleOverlaps: false, regionsOverlap: false, navigationOverlaps: false, controlsOverlap: false });
    const screenshot = await page.screenshot();
    assert.ok(screenshot.length > 10000);
  }
  assert.equal(await page.getByRole('button', { name: 'System theme', exact: true }).getAttribute('aria-pressed'), 'true');
  await page.getByRole('button', { name: 'Light theme', exact: true }).click();
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).backgroundColor), 'rgb(250, 252, 252)');
  assert.equal(await page.getByRole('button', { name: 'Light theme', exact: true }).getAttribute('aria-pressed'), 'true');
  await page.reload();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'light');
  await page.getByRole('button', { name: 'Dark theme', exact: true }).focus();
  await page.keyboard.press('Enter');
  await page.emulateMedia({ colorScheme: 'light' });
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).backgroundColor), 'rgb(24, 27, 29)');
  await page.reload();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'dark');
  await page.getByRole('button', { name: 'System theme', exact: true }).click();
  assert.equal(await page.evaluate(() => localStorage.getItem('demonstration.theme')), null);
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).backgroundColor), 'rgb(250, 252, 252)');
  await page.emulateMedia({ colorScheme: 'dark' });
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).backgroundColor), 'rgb(24, 27, 29)');
  await page.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('Storage blocked', 'SecurityError'); } }); });
  await page.reload();
  await page.getByRole('button', { name: 'Light theme', exact: true }).click();
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).backgroundColor), 'rgb(250, 252, 252)');
  assert.deepEqual(errors, []);
  const evidence = run.steps[0].artifacts[0];
  await writeFile(path.join(root, evidence.file), 'changed');
  await assert.rejects(renderDeck(root, run), /integrity/);
});

test('renders failure evidence with warnings for unavailable line callouts', async (context) => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), 'demonstration-callout-failure-'));
  context.after(() => rm(workspace, { recursive: true, force: true }));
  const steps = [
    { id: 'empty', argv: [process.execPath, '-e', 'console.error("compiler failed"); process.exitCode=1'], callouts: [{ type: 'lines', start: 1, end: 1, label: 'Build result' }] },
    { id: 'short', argv: [process.execPath, '-e', 'console.log("partial result"); process.exitCode=2'], callouts: [{ type: 'lines', start: 1, end: 1, label: 'Available output' }, { type: 'lines', start: 2, end: 4, label: '<missing output>' }] },
    { id: 'limits', argv: [process.execPath, '-e', 'console.log(Array.from({length:350}, (unused, index) => String(index + 1)).join("\\n"))'], callouts: [{ type: 'lines', start: 1, end: 102, label: 'Oversized range' }, { type: 'lines', start: 25, end: 125, label: 'First context' }, { type: 'lines', start: 130, end: 230, label: 'Excess context' }] },
  ].map((step) => ({ ...step, kind: 'command', title: 'Line annotation fixture', rationale: 'A missing annotation must not suppress captured evidence' }));
  const { root, run, deck } = await runPlan({ version: 1, title: 'Failure annotations', workspace, steps }, { output: path.join(workspace, 'run') });
  assert.deepEqual(run.steps.map((step) => step.status), ['failed', 'failed', 'passed']);
  assert.deepEqual(run.steps.map((step) => step.source.exitCode), [1, 2, 0]);
  const original = JSON.stringify(run);
  assert.equal(await main(['build', '--run', root]), 1);
  assert.equal(JSON.stringify(await loadRun(root)), original);
  const browser = await chromium.launch({ headless: true });
  context.after(() => browser.close());
  const page = await browser.newPage();
  await page.goto(pathToFileURL(deck).href);
  await page.waitForFunction(() => window.demonstrationDeck?.isReady());
  const empty = page.locator('section[data-artifact="empty-02"]');
  assert.equal(await empty.locator('.empty-evidence').textContent(), '(No output)');
  assert.match(await empty.locator('.annotation-warning').textContent(), /Build result.*0 captured lines/);
  assert.match(await page.locator('section[data-artifact="empty-01"] .code-evidence').textContent(), /compiler failed/);
  const short = page.locator('section[data-artifact="short-02"]');
  assert.equal(await short.locator('.highlighted').count(), 1);
  assert.match(await short.locator('.annotation-warning').textContent(), /<missing output>.*1 captured lines/);
  assert.equal(await short.locator('.annotation-warning missing').count(), 0);
  const limits = page.locator('section[data-artifact="limits-02"]');
  assert.equal(await limits.locator('.annotation-warning').count(), 2);
  assert.equal(await limits.locator('.highlighted').count(), 101);
  assert.ok(await limits.locator('.code-line').count() <= 240);
  const download = await short.locator('.download-evidence').getAttribute('href');
  assert.equal(Buffer.from(download.split(',')[1], 'base64').toString('utf8'), 'partial result\n');
});

test('preserves failure status, rejects dishonest results, and imports tool evidence as observed', async (context) => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), 'demonstration-failure-'));
  context.after(() => rm(workspace, { recursive: true, force: true }));
  const { root, run } = await runPlan({ version: 1, title: 'Failure', workspace, steps: [{ id: 'failure', kind: 'command', title: 'Fail', rationale: 'A failure must stay visible', argv: [process.execPath, '-e', 'process.exitCode=5'] }] }, { output: path.join(workspace, 'run') });
  assert.equal(run.steps[0].status, 'failed');
  assert.equal(await main(['build', '--run', root]), 1);
  const dishonest = structuredClone(run);
  dishonest.steps[0].status = 'passed';
  await assert.rejects(renderDeck(root, dishonest), /disagrees/);
  await writeFile(path.join(workspace, 'external.txt'), 'token=private\n');
  const event = { version: 1, tool: 'run_in_terminal', occurredAt: new Date().toISOString(), step: { id: 'external', kind: 'artifact', title: 'External result', rationale: 'Imported tool observation', file: 'external.txt', media: 'text' } };
  const appended = await appendEvent(event, { root, workspace });
  assert.equal(appended.run.steps[1].status, 'observed');
  assert.equal(appended.run.steps[1].source.tool, 'run_in_terminal');
  assert.ok(!(await readFile(path.join(root, appended.run.steps[1].artifacts[0].file), 'utf8')).includes('private'));
  await assert.rejects(appendEvent(event, { root, workspace }), /Duplicate/);
  await assert.rejects(withRunLock(root, () => withRunLock(root, () => {})), /locked/);
  await assert.rejects(runPlan({ version: 1, title: 'Existing', workspace, steps: [{ id: 'noop', kind: 'command', title: 'Noop', rationale: 'No overwrite', argv: [process.execPath, '--version'] }] }, { output: root }), /EEXIST/);
});
