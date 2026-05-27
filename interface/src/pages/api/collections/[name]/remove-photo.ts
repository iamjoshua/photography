import type { APIRoute } from 'astro';
import { runScript } from '../../../../lib/runScript';

/**
 * Remove a photo from a collection. Delegates to `scripts/remove-from-collection`.
 */
export const POST: APIRoute = async ({ params, request }) => {
  const name = params.name;
  if (!name) return new Response('missing name', { status: 400 });

  const body = await request.json().catch(() => ({}));
  const photoPath = body?.path;
  if (typeof photoPath !== 'string' || !photoPath) {
    return new Response('missing path', { status: 400 });
  }

  const result = await runScript('atomic/remove-from-collection', [name, photoPath]);
  if (!result.ok) {
    return new Response(result.stderr || result.stdout || 'remove failed', {
      status: 500,
    });
  }
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'content-type': 'application/json' },
  });
};
