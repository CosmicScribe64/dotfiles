import { lstat, mkdtemp, readFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { chromium } from 'playwright';
import { expect } from '@playwright/test';
import { allowedUrl } from './capture.mjs';
import { MAX_ARTIFACT_BYTES } from './evidence.mjs';

export async function captureUI(step, { result, add, allowedOrigins, env }) {
  const url = allowedUrl(step.url, allowedOrigins);
  const viewport = step.viewport ?? { width: 1280, height: 800 };
  const timeoutMs = step.timeoutMs ?? 30000;
  const masks = ['input[type="password"]', '[data-demo-private]', ...(step.mask ?? []), ...step.actions.filter((action) => action.valueEnv).map((action) => action.selector)];
  const videoDirectory = step.video ? await mkdtemp(path.join(os.tmpdir(), 'demonstration-video-')) : undefined;
  let browser;
  let context;
  let page;
  let timer;
  let timedOut = false;
  let consoleBytes = 0;
  let consoleDiscarded = false;
  const consoleLines = [];
  const pageErrors = [];
  const blockedOrigins = new Set();
  const interactions = new Set(['click', 'check', 'uncheck', 'fill', 'press', 'select', 'reload']);
  const interactionCount = step.actions.filter((action) => interactions.has(action.op)).length;
  const pauseMs = step.video ? Math.min(650, Math.floor(2400 / Math.max(1, interactionCount))) : 0;
  let recordingStartedAt;
  let captureDeadline;
  const permits = (input) => {
    try {
      const requested = new URL(input);
      if (['data:', 'blob:', 'about:'].includes(requested.protocol)) return true;
      if (requested.protocol === 'ws:') requested.protocol = 'http:';
      if (requested.protocol === 'wss:') requested.protocol = 'https:';
      allowedUrl(requested, allowedOrigins);
      return true;
    } catch {
      try { blockedOrigins.add(new URL(input).origin); } catch { blockedOrigins.add('invalid URL'); }
      return false;
    }
  };
  result.source = { url: url.href, viewport, video: Boolean(step.video), sanitized: Boolean(step.sanitized) };
  const snapshot = async (label, phase) => {
    const callouts = (step.callouts ?? []).filter((callout) => callout.type !== 'selector');
    for (const callout of (step.callouts ?? []).filter((item) => item.type === 'selector')) {
      const locator = page.locator(callout.selector);
      const count = await locator.count();
      if (count > 1) throw new Error(`Callout selector is ambiguous: ${callout.selector}`);
      const bounds = count ? await locator.boundingBox() : null;
      if (!bounds) continue;
      const left = Math.max(0, bounds.x);
      const top = Math.max(0, bounds.y);
      const right = Math.min(viewport.width, bounds.x + bounds.width);
      const bottom = Math.min(viewport.height, bounds.y + bounds.height);
      if (right > left && bottom > top) callouts.push({ type: 'box', label: callout.label, x: left / viewport.width, y: top / viewport.height, width: (right - left) / viewport.width, height: (bottom - top) / viewport.height });
    }
    const image = await page.screenshot({ animations: 'disabled', caret: 'hide', mask: masks.map((selector) => page.locator(selector)), maskColor: '#25282b', timeout: Math.min(timeoutMs, 10000) });
    await add('image', image, label, phase, callouts);
  };
  try {
    browser = await chromium.launch({ headless: true, timeout: timeoutMs, executablePath: env.DEMONSTRATION_CHROMIUM || undefined });
    context = await browser.newContext({
      viewport, deviceScaleFactor: 1, locale: 'en-US', timezoneId: 'UTC', reducedMotion: 'reduce', colorScheme: 'light',
      serviceWorkers: 'block', acceptDownloads: false,
      ...(videoDirectory ? { recordVideo: { dir: videoDirectory, size: viewport } } : {}),
    });
    captureDeadline = Date.now() + timeoutMs;
    timer = setTimeout(() => { timedOut = true; void context.close().catch(() => {}); }, timeoutMs);
    context.setDefaultTimeout(Math.min(timeoutMs, 5000));
    await context.route('**/*', (route) => permits(route.request().url()) ? route.continue() : route.abort('blockedbyclient'));
    await context.routeWebSocket('**/*', (socket) => { if (permits(socket.url())) socket.connectToServer(); else socket.close(); });
    if (step.video) await context.addInitScript((selectors) => {
      const attach = () => {
        if (!document.documentElement || document.getElementById('demonstration-masks')) return;
        const style = document.createElement('style');
        style.id = 'demonstration-masks';
        style.textContent = selectors.map((selector) => `${selector} { opacity: 0 !important; }`).join('\n');
        document.documentElement.append(style);
      };
      new MutationObserver(attach).observe(document, { childList: true, subtree: true });
      attach();
    }, masks);
    page = await context.newPage();
    recordingStartedAt = Date.now();
    page.on('console', (message) => {
      const text = `${message.type()}: ${message.text()}`;
      consoleBytes += Buffer.byteLength(text);
      if (consoleBytes > 1048576) { consoleDiscarded = true; consoleLines.length = 0; }
      else if (!consoleDiscarded) consoleLines.push(text);
    });
    page.on('pageerror', (error) => { if (pageErrors.length < 20) pageErrors.push(error.message); });
    const response = await page.goto(url.href, { waitUntil: 'domcontentloaded' });
    if (response && response.status() >= 400) throw new Error(`UI navigation returned HTTP ${response.status()}`);
    await snapshot('Before interaction', 'before');
    if (step.video) await page.waitForTimeout(650);
    for (const action of step.actions) {
      const locator = action.selector ? page.locator(action.selector) : undefined;
      if (action.op === 'snapshot') await snapshot(action.label, 'after');
      else if (action.op === 'reload') await page.reload({ waitUntil: 'domcontentloaded' });
      else if (action.op === 'fill') await locator.fill(action.valueEnv ? env[action.valueEnv] : action.value);
      else if (action.op === 'press') await locator.press(action.value);
      else if (action.op === 'select') await locator.selectOption(action.value);
      else if (['click', 'check', 'uncheck'].includes(action.op)) await locator[action.op]();
      else {
        const check = { label: `${action.selector} ${action.op === 'expectText' ? 'has expected text' : 'is visible'}`, expected: action.text ?? true, passed: false };
        result.checks.push(check);
        if (action.op === 'expectText') {
          await expect(locator).toHaveText(action.text, { timeout: Math.min(timeoutMs, 5000) });
          check.actual = await locator.textContent();
        } else {
          await expect(locator).toBeVisible({ timeout: Math.min(timeoutMs, 5000) });
          check.actual = true;
        }
        check.passed = true;
      }
      if (pauseMs && interactions.has(action.op)) await page.waitForTimeout(pauseMs);
    }
    await snapshot('After interaction', 'after');
    if (step.video) {
      const remaining = Math.max(0, captureDeadline - Date.now() - 500);
      const hold = Math.min(remaining, Math.max(1200, 5000 - (Date.now() - recordingStartedAt)));
      if (hold) await page.waitForTimeout(hold);
    }
    if (pageErrors.length) throw new Error('The page raised an uncaught JavaScript error');
    if (blockedOrigins.size) throw new Error('The page requested an unapproved origin');
    if (consoleDiscarded) throw new Error('Browser console exceeded the byte limit');
  } catch (error) {
    result.error = timedOut ? 'UI capture timed out' : error.message;
    if (page && !page.isClosed()) {
      try { await snapshot('Failure state', 'failure'); } catch (failure) { result.source.screenshotError = failure.message; }
    }
  } finally {
    clearTimeout(timer);
    result.source.blockedOrigins = [...blockedOrigins];
    await context?.close().catch((error) => { result.error ??= error.message; });
    try {
      if (step.video && page?.video()) {
        const file = await page.video().path();
        if ((await lstat(file)).size > MAX_ARTIFACT_BYTES) throw new Error('Recording exceeds the byte limit');
        await add('video', await readFile(file), 'Interaction recording', 'recording', []);
      }
    } catch (error) { result.error ??= error.message; }
    await browser?.close().catch((error) => { result.error ??= error.message; });
    if (videoDirectory) await rm(videoDirectory, { recursive: true, force: true });
    await add('text', consoleDiscarded ? '[Console discarded: byte limit exceeded]' : [...consoleLines, ...pageErrors.map((error) => `pageerror: ${error}`)].join('\n'), 'Browser console');
  }
}
