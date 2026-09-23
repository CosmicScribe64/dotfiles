import { readFile } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const seedTasks = [
  { id: 'task-1', title: 'Review the API contract', completed: false },
  { id: 'task-2', title: 'Check the mobile layout', completed: false },
  { id: 'task-3', title: 'Capture the baseline', completed: true },
];

export async function startExample() {
  const assets = new Map([
    ['/', { type: 'text/html; charset=utf-8', bytes: await readFile(new URL('./app.html', import.meta.url)) }],
    ['/filter.mjs', { type: 'text/javascript; charset=utf-8', bytes: await readFile(new URL('./filter.mjs', import.meta.url)) }],
    ['/font.woff2', { type: 'font/woff2', bytes: await readFile(new URL('../node_modules/@fontsource-variable/public-sans/files/public-sans-latin-wght-normal.woff2', import.meta.url)) }],
    ['/api/tasks', { type: 'application/json', bytes: Buffer.from(JSON.stringify({ tasks: seedTasks })) }],
  ]);
  const server = http.createServer((request, response) => {
    response.setHeader('X-Content-Type-Options', 'nosniff');
    response.setHeader('Cache-Control', 'no-store');
    if (![`127.0.0.1:${server.address().port}`, `localhost:${server.address().port}`].includes(request.headers.host)) {
      response.writeHead(403); response.end(); return;
    }
    if (request.method !== 'GET') { response.writeHead(405); response.end(); return; }
    const pathname = new URL(request.url, 'http://127.0.0.1').pathname;
    if (pathname === '/favicon.ico') { response.writeHead(204); response.end(); return; }
    const asset = assets.get(pathname);
    if (!asset) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { 'Content-Type': asset.type });
    response.end(asset.bytes);
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  return {
    url: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise((resolve, reject) => {
      server.closeAllConnections();
      server.close((error) => error ? reject(error) : resolve());
    }),
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  startExample().then((server) => {
    console.log(`Example: ${server.url}`);
    for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => { void server.close(); });
  }).catch((error) => { console.error(error.message); process.exitCode = 1; });
}
