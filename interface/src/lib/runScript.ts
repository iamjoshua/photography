import { spawn } from 'node:child_process';
import type { ChildProcessWithoutNullStreams } from 'node:child_process';
import path from 'node:path';
import { REPO_ROOT, SCRIPTS_DIR } from './paths';

export interface ScriptResult {
  ok: boolean;
  code: number;
  stdout: string;
  stderr: string;
}

function spawnIn(name: string, args: string[]): ChildProcessWithoutNullStreams {
  const scriptPath = path.join(SCRIPTS_DIR, name);
  return spawn(scriptPath, args, {
    cwd: REPO_ROOT,
    // Force Python wrappers to flush stdout/stderr line-by-line so the
    // streaming endpoint can show progress as it happens.
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  });
}

/**
 * Invoke a script under `scripts/` and buffer its output. The CLI is the
 * source of truth for all mutations; this is the only place in the
 * interface that touches state.
 */
export function runScript(
  name: string,
  args: string[] = [],
): Promise<ScriptResult> {
  return new Promise((resolve) => {
    const child = spawnIn(name, args);
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => {
      stdout += d.toString();
    });
    child.stderr.on('data', (d) => {
      stderr += d.toString();
    });
    child.on('close', (code) => {
      resolve({ ok: code === 0, code: code ?? -1, stdout, stderr });
    });
    child.on('error', (err) => {
      resolve({
        ok: false,
        code: -1,
        stdout,
        stderr: stderr + (stderr ? '\n' : '') + String(err),
      });
    });
  });
}

/**
 * Spawn a script and return a streaming Response that emits stdout/stderr
 * chunks as they arrive, plus a final sentinel line `__DONE__:<exitCode>`.
 * Used for long-running workflows where the UI needs live progress.
 *
 * If the client disconnects mid-run, the spawned child keeps running so
 * the work completes — but we stop pushing to the dead stream to avoid
 * an unhandled ERR_INVALID_STATE.
 */
export function streamScript(name: string, args: string[] = []): Response {
  const encoder = new TextEncoder();
  let closed = false;

  const stream = new ReadableStream({
    start(controller) {
      const safeEnqueue = (chunk: Uint8Array | Buffer): void => {
        if (closed) return;
        try {
          controller.enqueue(chunk);
        } catch {
          closed = true;
        }
      };
      const safeClose = (): void => {
        if (closed) return;
        closed = true;
        try {
          controller.close();
        } catch {
          // already closed by the reader cancelling
        }
      };

      let child: ChildProcessWithoutNullStreams;
      try {
        child = spawnIn(name, args);
      } catch (err) {
        safeEnqueue(encoder.encode(`Error spawning: ${String(err)}\n__DONE__:-1\n`));
        safeClose();
        return;
      }
      child.stdout.on('data', safeEnqueue);
      child.stderr.on('data', safeEnqueue);
      child.on('close', (code) => {
        safeEnqueue(encoder.encode(`\n__DONE__:${code ?? -1}\n`));
        safeClose();
      });
      child.on('error', (err) => {
        safeEnqueue(encoder.encode(`\nError: ${String(err)}\n__DONE__:-1\n`));
        safeClose();
      });
    },
    cancel() {
      // Reader bailed (browser refresh, network blip). Stop trying to
      // push to the stream. The child keeps running because the
      // underlying scripts are idempotent and the user will see results
      // on their next page load.
      closed = true;
    },
  });
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache',
      'X-Accel-Buffering': 'no',
    },
  });
}
