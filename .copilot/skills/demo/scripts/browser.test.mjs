import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import test from 'node:test';
import { chromium } from 'playwright';
import { captureStep } from './capture.mjs';
import { loadArtifact } from './evidence.mjs';
import { renderDeck } from './render.mjs';

test('browser captures assertions, checkpoint images, console output, and a finalized recording', async (context) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'demonstration-browser-'));
  const server = http.createServer((request, response) => {
    response.setHeader('content-type', 'text/html');
    response.end('<!doctype html><html><head><title>Capture fixture</title></head><body><main><h1>Preference</h1><button onclick="document.querySelector(\'output\').textContent=\'Saved\'; console.log(\'saved\')">Save</button><output>Unsaved</output><input type="password" value="never-visible"></main></body></html>');
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  context.after(async () => { server.closeAllConnections(); await new Promise((resolve) => server.close(resolve)); await rm(root, { recursive: true, force: true }); });
  const step = {
    id: 'save', title: 'Save preference', rationale: 'The visible result must follow the click', kind: 'ui',
    url: `http://127.0.0.1:${server.address().port}`, video: true, sanitized: true,
    callouts: [{ type: 'selector', selector: 'output', label: 'Saved state' }],
    actions: [{ op: 'expectText', selector: 'output', text: 'Unsaved' }, { op: 'click', selector: 'button' }, { op: 'expectText', selector: 'output', text: 'Saved' }, { op: 'snapshot', label: 'Saved checkpoint' }],
  };
  const result = await captureStep(step, { root, workspace: root });
  assert.equal(result.status, 'passed', result.error);
  assert.equal(result.checks.length, 2);
  const images = result.artifacts.filter((artifact) => artifact.type === 'image');
  assert.equal(images.length, 3);
  assert.notEqual(images[0].sha256, images[1].sha256);
  assert.equal(images[1].sha256, images[2].sha256);
  assert.equal(images[1].callouts[0].type, 'box');
  for (const artifact of result.artifacts) await loadArtifact(root, artifact);
  const recording = result.artifacts.find((artifact) => artifact.type === 'video');
  assert.ok(recording.bytes > 1000);
  const consoleArtifact = result.artifacts.find((artifact) => artifact.type === 'text');
  assert.match(await readFile(path.join(root, consoleArtifact.file), 'utf8'), /log: saved/);
  const git = { head: null, dirty: null, capturedAt: result.finishedAt };
  const deck = await renderDeck(root, { version: 1, title: 'Browser fixture', state: 'complete', startedAt: result.startedAt, finishedAt: result.finishedAt, planSha256: '0'.repeat(64), repository: { before: git, after: git }, steps: [result] });
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(deck).href);
    await page.evaluate(() => window.demonstrationDeck.slide(1));
    await page.waitForFunction(() => document.querySelector('video').readyState >= 2, undefined, { timeout: 5000 });
    await page.evaluate(async () => { const video = document.querySelector('video'); video.muted = true; await video.play(); });
    await page.waitForFunction(() => document.querySelector('video').currentTime > 0, undefined, { polling: 50, timeout: 3000 });
    const videoState = await page.locator('video').evaluate((video) => ({ width: video.videoWidth, height: video.videoHeight, duration: video.duration, error: video.error }));
    assert.equal(videoState.width, 1280);
    assert.equal(videoState.height, 800);
    assert.ok(videoState.duration >= 4, `The recording is too fast to follow: ${videoState.duration}s`);
    assert.equal(videoState.error, null);
  } finally { await browser.close(); }
  const failure = await captureStep({ ...step, id: 'failure', video: false, timeoutMs: 800, actions: [{ op: 'expectText', selector: 'output', text: 'Wrong' }] }, { root, workspace: root });
  assert.equal(failure.status, 'failed');
  assert.equal(failure.checks[0].passed, false);
  assert.ok(failure.artifacts.some((artifact) => artifact.phase === 'failure'));
});
