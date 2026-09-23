import { createHash } from 'node:crypto';
import { open, readFile, rename, unlink } from 'node:fs/promises';
import path from 'node:path';
import lucide from 'lucide';
import { loadArtifact } from './evidence.mjs';
import { validate } from './validate.mjs';

const mimeTypes = { text: 'text/plain', json: 'application/json', diff: 'text/plain', image: 'image/png', video: 'video/webm' };
const extensions = { text: 'txt', json: 'json', diff: 'diff', image: 'png', video: 'webm' };

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

function themeControls() {
  const choices = [['system', 'System theme', lucide.Monitor], ['light', 'Light theme', lucide.Sun], ['dark', 'Dark theme', lucide.Moon]];
  return `<div class="theme-controls" role="group" aria-label="Color theme">${choices.map(([mode, label, nodes]) => {
    const shapes = nodes.map(([tag, attributes]) => `<${tag} ${Object.entries(attributes).map(([key, value]) => `${key}="${escapeHtml(value)}"`).join(' ')}></${tag}>`).join('');
    return `<button type="button" class="theme-button" data-theme-choice="${mode}" aria-label="${label}" aria-pressed="${mode === 'system'}"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${shapes}</svg><span class="theme-tooltip" role="tooltip">${label}</span></button>`;
  }).join('')}</div>`;
}

function codeEvidence(bytes, artifact) {
  const lines = bytes.toString('utf8').split('\n');
  if (lines.at(-1) === '') lines.pop();
  const ranges = [];
  const warnings = [];
  const visible = new Set();
  for (let index = 0; index < Math.min(lines.length, 24); index++) visible.add(index);
  for (let index = Math.max(0, lines.length - 12); index < lines.length; index++) visible.add(index);
  for (const [calloutIndex, range] of artifact.callouts.entries()) {
    if (range.type !== 'lines') continue;
    let warning;
    const expanded = new Set(visible);
    if (range.end > lines.length) warning = `lines ${range.start}-${range.end} exceed the ${lines.length} captured lines`;
    else if (range.end - range.start > 100) warning = 'the range exceeds the 101-line limit';
    else {
      for (let index = Math.max(0, range.start - 3); index < Math.min(lines.length, range.end + 2); index++) expanded.add(index);
      if (expanded.size > 240) warning = 'the excerpt would exceed the 240-line display limit';
    }
    if (warning) {
      warnings.push(`Callout ${calloutIndex + 1} (${range.label}) not highlighted: ${warning}.`);
      continue;
    }
    ranges.push(range);
    for (const index of expanded) visible.add(index);
  }
  const annotations = warnings.map((warning) => `<p class="annotation-warning evidence-caption" role="note">Annotation warning: ${escapeHtml(warning)}</p>`).join('');
  if (!lines.length) return `<p class="empty-evidence">(No output)</p>${annotations}`;
  let previous = -1;
  const rendered = [...visible].sort((left, right) => left - right).map((index) => {
    const omission = index > previous + 1 ? `<span class="omission">${index - previous - 1} lines omitted from this slide</span>` : '';
    previous = index;
    const highlighted = ranges.some((range) => index + 1 >= range.start && index + 1 <= range.end);
    return `${omission}<span class="code-line${highlighted ? ' highlighted' : ''}" data-line="${index + 1}"><span class="line-number" aria-hidden="true">${index + 1}</span><span>${escapeHtml(lines[index]) || ' '}</span></span>`;
  });
  return `${annotations}<pre class="code-evidence" tabindex="0"><code>${rendered.join('')}</code></pre><p class="evidence-caption">${lines.length} source lines; ${visible.size} shown. Highlighted line numbers refer to the captured artifact.</p>`;
}

function mediaEvidence(bytes, artifact, dataUrl) {
  if (artifact.type === 'video') {
    if (!bytes.subarray(0, 4).equals(Buffer.from('1a45dfa3', 'hex'))) throw new Error('Invalid WebM evidence');
    return `<video controls playsinline preload="metadata" aria-label="${escapeHtml(artifact.label)}" src="${dataUrl}"></video><p class="media-error" role="status" hidden>This browser could not decode the recording. Open the deck in Chrome or Firefox, or download the original evidence.</p>`;
  }
  if (bytes.length < 24 || bytes.subarray(12, 16).toString() !== 'IHDR'
      || !bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex'))) throw new Error('Invalid PNG evidence');
  const width = bytes.readUInt32BE(16);
  const height = bytes.readUInt32BE(20);
  if (!width || !height || width > 20000 || height > 20000) throw new Error('Invalid PNG dimensions');
  const boxes = artifact.callouts.flatMap((box, index) => box.type === 'box'
    ? [`<span class="callout-box" style="left:${box.x * 100}%;top:${box.y * 100}%;width:${box.width * 100}%;height:${box.height * 100}%" aria-label="${escapeHtml(box.label)}"><span>${index + 1}</span></span>`] : []).join('');
  return `<div class="image-evidence" style="aspect-ratio:${width}/${height}"><img width="${width}" height="${height}" src="${dataUrl}" alt="${escapeHtml(artifact.label)}">${boxes}</div>`;
}

function findings(step) {
  if (!step.checks.length) return '<p class="unverified">Observation only. No behavioral assertion was evaluated.</p>';
  return `<ul class="checks">${step.checks.map((check) => {
    const details = Object.hasOwn(check, 'expected') ? `Expected: ${JSON.stringify(check.expected)}; actual: ${Object.hasOwn(check, 'actual') ? JSON.stringify(check.actual) : 'not obtained'}` : '';
    return `<li><strong class="${check.passed ? 'passed' : 'failed'}">${check.passed ? 'PASS' : 'FAIL'}</strong> ${escapeHtml(check.label)}<small>${escapeHtml(details.slice(0, 500))}${details.length > 500 ? ' (excerpt)' : ''}</small></li>`;
  }).join('')}</ul>`;
}

export async function renderDeck(root, run) {
  validate('run', run);
  let totalBytes = 0;
  const slides = [];
  const hasUi = run.steps.some((step) => step.kind === 'ui');
  const counts = { passed: 0, failed: 0, observed: 0 };
  for (const step of run.steps) counts[step.status]++;
  for (const [stepIndex, step] of run.steps.entries()) {
    const hasCheckpoint = step.artifacts.some((artifact) => artifact.type === 'image' && artifact.phase === 'after' && artifact.label !== 'After interaction');
    for (const artifact of step.artifacts) {
      if (artifact.file !== `artifacts/${artifact.id}.${extensions[artifact.type]}`) throw new Error('Artifact type, id, and path disagree');
      totalBytes += artifact.bytes;
      if (totalBytes > 67108864) throw new Error('Deck evidence exceeds 64 MiB; split the run');
      const bytes = await loadArtifact(root, artifact);
      if (!bytes.length && !artifact.callouts.length && step.status !== 'failed' && !['image', 'video'].includes(artifact.type)) continue;
      if (step.status !== 'failed') {
        if (step.kind === 'ui' && artifact.type !== 'video' && (artifact.type !== 'image' || artifact.phase !== 'after' || (hasCheckpoint && artifact.label === 'After interaction'))) continue;
        if (hasUi && !['ui', 'artifact'].includes(step.kind) && !artifact.callouts.length) continue;
      }
      const dataUrl = `data:${mimeTypes[artifact.type]};base64,${bytes.toString('base64')}`;
      const media = ['image', 'video'].includes(artifact.type);
      if (artifact.callouts.some((callout) => (callout.type === 'box' && artifact.type !== 'image') || (callout.type === 'lines' && media))) throw new Error('Callout does not match evidence type');
      const visual = media ? mediaEvidence(bytes, artifact, dataUrl) : codeEvidence(bytes, artifact);
      const status = ['before', 'recording', 'imported'].includes(artifact.phase) ? 'observed' : step.status;
      const callouts = artifact.callouts.map((callout, index) => `<li><span class="callout-number">${index + 1}</span>${escapeHtml(callout.label)}${callout.type === 'lines' ? ` <small>Lines ${callout.start}-${callout.end}</small>` : ''}</li>`).join('');
      slides.push(`<section class="demo-slide" data-step="${step.id}" data-artifact="${artifact.id}">
<header class="title-block"><p class="feature-context">${escapeHtml(run.title)}<span class="draft-label">${run.state === 'complete' ? 'Review draft' : 'Incomplete run'}</span></p><div class="step-title"><h2>${escapeHtml(step.title)}</h2><span class="status ${status}">${status}</span></div><p class="artifact-context">Step ${stepIndex + 1} of ${run.steps.length} / ${escapeHtml(artifact.label)}</p></header>
<div class="slide-body"><main class="evidence-deck" aria-label="Evidence">${visual}<a class="download-evidence" href="${dataUrl}" download="${artifact.id}.${extensions[artifact.type]}">Download full evidence</a></main>
<aside class="agent-commentary"><h3>Rationale</h3><p>${escapeHtml(step.rationale)}</p><h3>Verification Findings</h3>${findings(step)}${step.error ? `<p class="error-message">${escapeHtml(step.error)}</p>` : ''}${callouts ? `<h3>Callouts</h3><ol class="callout-list">${callouts}</ol>` : ''}<h3>Edge Cases</h3>${step.edgeCases.length ? `<ul>${step.edgeCases.map((note) => `<li>${escapeHtml(note)}</li>`).join('')}</ul>` : '<p class="unverified">No additional edge cases declared.</p>'}<details><summary>Capture provenance</summary><pre>${escapeHtml(JSON.stringify({ artifactSavedAt: artifact.savedAt, stepStartedAt: step.startedAt, stepFinishedAt: step.finishedAt, phase: artifact.phase, source: step.source, sha256: artifact.sha256 }, null, 2))}</pre></details></aside></div>
<footer class="slide-footer"><span>${counts.passed} passed / ${counts.failed} failed / ${counts.observed} observed steps</span><span>HEAD ${escapeHtml(run.repository.after.head?.slice(0, 12) ?? 'unavailable')} / dirty: ${run.repository.after.dirty ?? 'unknown'}</span></footer>
</section>`);
    }
  }
  const [revealCss, revealJs, deckCss, deckJs, themeJs, font, revealLicense, fontLicense, iconLicense] = await Promise.all([
    readFile(new URL('../node_modules/reveal.js/dist/reveal.css', import.meta.url), 'utf8'),
    readFile(new URL('../node_modules/reveal.js/dist/reveal.js', import.meta.url), 'utf8'),
    readFile(new URL('../assets/deck.css', import.meta.url), 'utf8'),
    readFile(new URL('../assets/deck.js', import.meta.url), 'utf8'),
    readFile(new URL('../assets/theme.js', import.meta.url), 'utf8'),
    readFile(new URL('../node_modules/@fontsource-variable/public-sans/files/public-sans-latin-wght-normal.woff2', import.meta.url)),
    readFile(new URL('../node_modules/reveal.js/LICENSE', import.meta.url), 'utf8'),
    readFile(new URL('../node_modules/@fontsource-variable/public-sans/LICENSE', import.meta.url), 'utf8'),
    readFile(new URL('../node_modules/lucide/LICENSE', import.meta.url), 'utf8'),
  ]);
  const scripts = [themeJs, revealJs, deckJs].map((script) => script.replace(/<\/script/gi, '<\\/script'));
  const hashes = scripts.map((script) => `'sha256-${createHash('sha256').update(script).digest('base64')}'`).join(' ');
  const policy = `default-src 'none'; script-src ${hashes}; style-src 'unsafe-inline'; font-src data:; img-src data:; media-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'`;
  const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="${escapeHtml(policy)}"><script>${scripts[0]}</script><title>${escapeHtml(run.title)} | Demonstration</title><style>${revealCss}\n@font-face{font-family:Public Sans;src:url(data:font/woff2;base64,${font.toString('base64')}) format('woff2');font-weight:100 900;font-style:normal;font-display:swap;}\n${deckCss}</style></head><body><div class="reveal"><div class="slides">${slides.join('\n')}</div></div>${themeControls()}<template id="third-party-notices"><pre>${escapeHtml(`${revealLicense}\n\n${fontLicense}\n\n${iconLicense}`)}</pre></template>${scripts.slice(1).map((script) => `<script>${script}</script>`).join('')}</body></html>\n`;
  const temporary = path.join(root, 'index.html.next');
  const handle = await open(temporary, 'wx', 0o600);
  try {
    await handle.writeFile(html);
    await handle.close();
    await rename(temporary, path.join(root, 'index.html'));
  } finally {
    await handle.close();
    await unlink(temporary).catch((error) => { if (error.code !== 'ENOENT') throw error; });
  }
  return path.join(root, 'index.html');
}
