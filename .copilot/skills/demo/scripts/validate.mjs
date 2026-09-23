import { readFileSync } from 'node:fs';
import Ajv from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const validator = new Ajv({ allErrors: true, strict: true, strictRequired: false });
addFormats(validator);
for (const name of ['plan', 'run', 'hook']) {
  validator.addSchema(JSON.parse(readFileSync(new URL(`../schemas/${name}.schema.json`, import.meta.url), 'utf8')));
}

export function outcome(step) {
  if (step.error || step.checks.some((check) => !check.passed)) return 'failed';
  return step.checks.length ? 'passed' : 'observed';
}

export function validate(name, value) {
  const check = validator.getSchema(`urn:demonstration:${name}`);
  if (!check || !check(value)) {
    throw new Error(`Invalid ${name}: ${validator.errorsText(check?.errors, { separator: '; ' })}`);
  }
  const steps = name === 'hook' ? [value.step] : value.steps;
  const ids = new Set();
  const files = new Set();
  for (const step of steps) {
    if (ids.has(step.id)) throw new Error(`Duplicate step id: ${step.id}`);
    ids.add(step.id);
    if (name === 'run' && step.status !== outcome(step)) throw new Error('Status disagrees with recorded checks');
    if (step.video && step.actions.some((action) => action.valueEnv)) {
      throw new Error('Recordings cannot include environment-sourced form values');
    }
    for (const artifact of step.artifacts ?? []) {
      if (files.has(artifact.file)) throw new Error('Duplicate artifact path');
      files.add(artifact.file);
    }
    for (const callout of [...(step.callouts ?? []), ...(step.artifacts ?? []).flatMap((artifact) => artifact.callouts)]) {
      if (callout.type === 'lines' && callout.end < callout.start) throw new Error('Invalid line range');
      if (callout.type === 'box' && (callout.x + callout.width > 1.000001 || callout.y + callout.height > 1.000001)) {
        throw new Error('Callout box exceeds image bounds');
      }
      if (callout.type === 'selector' && step.kind !== 'ui') throw new Error('Selector callouts require UI capture');
    }
  }
  return value;
}

export function parseJson(text) {
  return JSON.parse(text, (key, value) => {
    if (typeof value === 'number' && (!Number.isFinite(value) || (Number.isInteger(value) && !Number.isSafeInteger(value)))) {
      throw new Error('Unsafe JSON number; encode large identifiers as strings');
    }
    return value;
  });
}
