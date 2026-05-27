import type { APIRoute } from 'astro';
import { runScript } from '../../../../lib/runScript';

/**
 * Update a collection's title and/or description.
 * Delegates to `scripts/update-collection <name> [--title T] [--description D]`.
 */
export const POST: APIRoute = async ({ params, request }) => {
  const name = params.name;
  if (!name) return new Response('missing name', { status: 400 });

  const body = await request.json().catch(() => ({}));
  const { title, description } = body;

  const args: string[] = [name];
  if (typeof title === 'string') args.push('--title', title);
  if (typeof description === 'string') args.push('--description', description);

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
