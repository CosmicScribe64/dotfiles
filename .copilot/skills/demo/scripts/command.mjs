import { spawn } from 'node:child_process';

export function runCommand(argv, { cwd, env = process.env, timeoutMs = 30000, maxBytes = 1048576 } = {}) {
  return new Promise((resolve) => {
    const result = { stdout: '', stderr: '', exitCode: null, signal: null, timedOut: false, truncated: false };
    const buffers = { stdout: [], stderr: [] };
    const started = performance.now();
    let totalBytes = 0;
    const child = spawn(argv[0], argv.slice(1), {
      cwd, env, shell: false, detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'],
    });
    const stop = () => {
      if (!child.pid) return;
      try {
        if (process.platform === 'win32') child.kill('SIGKILL');
        else process.kill(-child.pid, 'SIGKILL');
      } catch (error) {
        if (error.code !== 'ESRCH') result.error = error.message;
      }
    };
    const timer = setTimeout(() => {
      result.timedOut = true;
      stop();
    }, timeoutMs);
    for (const stream of ['stdout', 'stderr']) {
      child[stream].on('data', (chunk) => {
        totalBytes += chunk.length;
        if (totalBytes > maxBytes) {
          result.truncated = true;
          buffers.stdout = [];
          buffers.stderr = [];
          stop();
        } else if (!result.truncated) buffers[stream].push(chunk);
      });
    }
    child.on('error', (error) => { result.error = error.message; });
    child.on('close', (exitCode, signal) => {
      clearTimeout(timer);
      stop();
      Object.assign(result, {
        exitCode, signal, durationMs: Math.round(performance.now() - started),
        stdout: result.truncated ? '[Output discarded: byte limit exceeded]\n' : Buffer.concat(buffers.stdout).toString('utf8'),
        stderr: result.truncated ? '[Output discarded: byte limit exceeded]\n' : Buffer.concat(buffers.stderr).toString('utf8'),
      });
      resolve(result);
    });
  });
}

export async function repositoryState(workspace) {
  const head = await runCommand(['git', 'rev-parse', '--verify', 'HEAD'], { cwd: workspace, timeoutMs: 3000 });
  const status = await runCommand(['git', 'status', '--porcelain=v1', '-z'], { cwd: workspace, timeoutMs: 3000 });
  return {
    head: head.exitCode === 0 && /^[a-f0-9]{40,64}$/.test(head.stdout.trim()) ? head.stdout.trim() : null,
    dirty: status.exitCode === 0 && !status.truncated ? Boolean(status.stdout) : null,
    capturedAt: new Date().toISOString(),
  };
}
