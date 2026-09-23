import { createHash } from 'node:crypto';
import { lstat, mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { stripVTControlCharacters } from 'node:util';

export const MAX_ARTIFACT_BYTES = 16 * 1024 * 1024;
const extensions = { text: 'txt', json: 'json', diff: 'diff', image: 'png', video: 'webm' };
const sensitiveKey = /(?:authorization|cookie|password|passwd|secret|token|api[_-]?key|connection[_-]?string)/i;

export function redactText(input, secrets = []) {
  let text = stripVTControlCharacters(String(input));
  for (const secret of [...new Set(secrets)].filter(Boolean).sort((left, right) => right.length - left.length)) {
    text = text.replaceAll(secret, '[REDACTED]');
  }
  return text
    .replace(/\b(Bearer|Basic)\s+[\w.+/=-]+/gi, '$1 [REDACTED]')
    .replace(/(?<![\w.-])((?=[\w.-]*(?:password|passwd|secret|token|api[_-]?key|authorization|cookie|connection[_-]?string))[\w.-]+["']?\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;&]+)/gi, '$1[REDACTED]')
    .replace(/(\b[a-z][a-z0-9+.-]*:\/\/)[^\s/@:]+:[^\s/@]+@/gi, '$1[REDACTED]@');
}

export function redactValue(value, secrets = [], keyPath = '') {
  if (sensitiveKey.test(stripVTControlCharacters(keyPath))) return '[REDACTED]';
  if (typeof value === 'string') return redactText(value, secrets);
  if (Array.isArray(value)) return value.map((item) => redactValue(item, secrets));
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [
      redactText(key, secrets), redactValue(item, secrets, key),
    ]));
  }
  return value;
}

export function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

export async function confinedFile(root, relativePath) {
  if (typeof relativePath !== 'string' || !relativePath || path.isAbsolute(relativePath)
      || relativePath.includes('\\') || relativePath.includes('\0')
      || relativePath.split('/').some((part) => !part || part === '.' || part === '..')) {
    throw new Error('Expected a confined relative file path');
  }
  const resolvedRoot = await realpath(root);
  let current = resolvedRoot;
  for (const part of relativePath.split('/')) {
    current = path.join(current, part);
    if ((await lstat(current)).isSymbolicLink()) throw new Error('Symlink evidence is not allowed');
  }
  if (!(await lstat(current)).isFile()) throw new Error('Evidence must be a regular file');
  return current;
}

export async function storeArtifact(root, id, type, content, secrets = []) {
  if (!/^[a-z][a-z0-9-]{0,79}$/.test(id) || !Object.hasOwn(extensions, type)) {
    throw new Error('Invalid artifact id or type');
  }
  const binary = type === 'image' || type === 'video';
  if (binary && !Buffer.isBuffer(content)) throw new Error('Binary evidence requires a Buffer');
  const bytes = binary ? content : Buffer.from(type === 'json'
    ? `${JSON.stringify(redactValue(JSON.parse(String(content)), secrets), null, 2)}\n`
    : redactText(content, secrets));
  if (bytes.length > MAX_ARTIFACT_BYTES) throw new Error('Artifact exceeds the byte limit');
  if (type === 'image' && !bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex'))) {
    throw new Error('Image evidence must be PNG');
  }
  if (type === 'video' && !bytes.subarray(0, 4).equals(Buffer.from('1a45dfa3', 'hex'))) {
    throw new Error('Video evidence must be WebM');
  }
  const directory = path.join(root, 'artifacts');
  await mkdir(directory, { recursive: true, mode: 0o700 });
  if ((await lstat(directory)).isSymbolicLink()) throw new Error('Symlink evidence is not allowed');
  const file = `artifacts/${id}.${extensions[type]}`;
  await writeFile(path.join(root, file), bytes, { flag: 'wx', mode: 0o600 });
  return { id, type, file, bytes: bytes.length, sha256: sha256(bytes), savedAt: new Date().toISOString() };
}

export async function loadArtifact(root, artifact) {
  if (!artifact.file?.startsWith('artifacts/')) throw new Error('Expected an artifact file');
  const file = await confinedFile(root, artifact.file);
  if ((await lstat(file)).size > MAX_ARTIFACT_BYTES) throw new Error('Artifact exceeds the byte limit');
  const bytes = await readFile(file);
  if (bytes.length !== artifact.bytes || sha256(bytes) !== artifact.sha256) {
    throw new Error(`Artifact integrity check failed: ${artifact.id}`);
  }
  return bytes;
}
