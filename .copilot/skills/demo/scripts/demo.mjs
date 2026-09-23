import { parseArgs } from 'node:util';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { redactText } from './evidence.mjs';
import { renderDeck } from './render.mjs';
import { appendEvent, loadRun, readJsonFile, runPlan, withRunLock } from './run.mjs';
import { validate } from './validate.mjs';

export async function main(argv = process.argv.slice(2)) {
  const { values, positionals } = parseArgs({ args: argv, allowPositionals: true, strict: true, options: {
    plan: { type: 'string' }, out: { type: 'string' }, run: { type: 'string' }, workspace: { type: 'string' },
    event: { type: 'string' }, 'secret-env': { type: 'string', multiple: true }, help: { type: 'boolean' },
  } });
  if (values.help) {
    console.log('Usage:\n  demo.mjs validate --plan FILE\n  demo.mjs run --plan FILE --out NEW_DIRECTORY\n  demo.mjs build --run DIRECTORY\n  demo.mjs append --run DIRECTORY --workspace DIRECTORY --event FILE [--secret-env NAME]');
    return 0;
  }
  const command = positionals[0];
  const required = { validate: ['plan'], run: ['plan', 'out'], build: ['run'], append: ['run', 'workspace', 'event'] };
  if (positionals.length !== 1 || !Object.hasOwn(required, command)) throw new Error('Expected validate, run, build, or append; use --help');
  const permitted = [...required[command], ...(command === 'append' ? ['secret-env'] : [])];
  if (Object.keys(values).some((key) => !permitted.includes(key))) throw new Error('Option does not apply to this command');
  for (const name of required[command]) if (!values[name]) throw new Error(`Missing --${name}`);
  if (command === 'validate') {
    const plan = validate('plan', await readJsonFile(path.resolve(values.plan)));
    console.log(`Valid plan: ${plan.steps.length} steps`);
    return 0;
  }
  if (command === 'build') {
    const root = path.resolve(values.run);
    const { run, deck } = await withRunLock(root, async () => {
      const run = await loadRun(root);
      return { run, deck: await renderDeck(root, run) };
    });
    console.log(`Evidence preview: ${deck}`);
    return run.state === 'complete' && run.steps.every((step) => step.status !== 'failed') ? 0 : 1;
  }
  const result = command === 'run'
    ? await runPlan(await readJsonFile(path.resolve(values.plan)), {
      output: values.out, baseDirectory: path.dirname(path.resolve(values.plan)),
      onStep: (step) => console.log(`${step.status.toUpperCase()}: ${step.id}`),
    })
    : await appendEvent(await readJsonFile(path.resolve(values.event)), {
      root: path.resolve(values.run), workspace: path.resolve(values.workspace), secretEnv: values['secret-env'] ?? [],
    });
  console.log(`Evidence preview: ${result.deck}\nManifest: ${path.join(result.root, 'run.json')}`);
  return result.run.steps.every((step) => step.status !== 'failed') && result.run.state === 'complete' ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().then((code) => { process.exitCode = code; }).catch((error) => {
    console.error(`Demonstration: ${redactText(error.message)}`);
    process.exitCode = 2;
  });
}
