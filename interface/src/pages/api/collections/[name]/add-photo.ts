import type { APIRoute } from 'astro';
import { runScript } from '../../../../lib/runScript';

/**
 * Add a photo to a collection. Delegates to `scripts/add-to-collection`.
 */
export const POST: APIRoute = async ({ params, request }) => {
  const name = params.name;
  if (!name) return new Response('missing name', { status: 400 });

  const body = await request.json().catch(() => ({}));
  const photoPath = body?.path;
  if (typeof photoPath !== 'string' || !photoPath) {
    return new Response('missing path', { status: 400 });
  }

  const result = await runScript('atomic/add-to-collection', [name, photoPath]);
  if (!result.ok) {
    return new Response(result.stderr || result.stdout || 'add failed', {
      status: 500,
    });
  }
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'content-type': 'application/json' },
  });
};
