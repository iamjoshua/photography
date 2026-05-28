import type { APIRoute } from 'astro';
import { runScript } from '../../../../lib/runScript';

/**
 * Update a collection's title, description, and/or cover photo.
 * Delegates to `scripts/atomic/update-collection <name> [--title T]
 * [--description D] [--cover-path PATH]`.
 */
export const POST: APIRoute = async ({ params, request }) => {
  const name = params.name;
  if (!name) return new Response('missing name', { status: 400 });

  const body = await request.json().catch(() => ({}));
  const { title, description, cover_path } = body;

  const args: string[] = [name];
  if (typeof title === 'string') args.push('--title', title);
  if (typeof description === 'string') args.push('--description', description);
  if (typeof cover_path === 'string') args.push('--cover-path', cover_path);

  if (args.length === 1) {
    return new Response('nothing to update', { status: 400 });
  }

  const result = await runScript('atomic/update-collection', args);
  if (!result.ok) {
    return new Response(result.stderr || result.stdout || 'update failed', {
      status: 500,
    });
  }
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'content-type': 'application/json' },
  });
};
