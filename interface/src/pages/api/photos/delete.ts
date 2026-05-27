import type { APIRoute } from 'astro';
import { runScript } from '../../../lib/runScript';

/**
 * Cascading delete of a single photo from the entire portfolio:
 *   photos/ jpg + data/photos/ yaml + r2/{small,large} + every collection ref.
 *
 * Delegates to `scripts/delete-photo <path>`. The script must perform the full
 * cascade — the interface never writes to data/ or r2/ directly.
 */
export const POST: APIRoute = async ({ request }) => {
  const body = await request.json().catch(() => ({}));
  const photoPath = body?.path;
  if (typeof photoPath !== 'string' || !photoPath) {
    return new Response('missing path', { status: 400 });
  }

  const result = await runScript('atomic/delete-photo', [photoPath]);
  if (!result.ok) {
    return new Response(result.stderr || result.stdout || 'delete failed', {
      status: 500,
    });
  }
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'content-type': 'application/json' },
  });
};
