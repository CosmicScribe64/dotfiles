// Local build only. Users running the prebuilt app do not need Node or npm.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);
const here=path.dirname(fileURLToPath(import.meta.url));
const root=process.env.TAILWIND_ROOT || path.dirname(require.resolve('tailwindcss/package.json'));
const {compile}=require(path.join(root,'dist/lib.js'));
const theme=fs.readFileSync(path.join(root,'theme.css'),'utf8');
const preflight=fs.readFileSync(path.join(root,'preflight.css'),'utf8');
const custom=fs.readFileSync(path.join(here,'assets/app.css'),'utf8');
const input=`@layer theme, base, components, utilities;\n@layer theme {${theme}}\n@layer base {${preflight}}\n@layer utilities {@tailwind utilities;}\n${custom}`;
const corpus=['static/index.html','static/app.js','server.py'].map(f=>fs.readFileSync(path.join(here,f),'utf8')).join('\n');
const candidates=[...new Set(corpus.match(/[A-Za-z0-9_:/.[\]%-]+/g)||[])];
const compiler=await compile(input);
fs.writeFileSync(path.join(here,'static/styles.css'),compiler.build(candidates));
console.log('Built static/styles.css locally.');
