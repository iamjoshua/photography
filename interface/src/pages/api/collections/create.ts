import type { APIRoute } from 'astro';
import { runScript } from '../../../lib/runScript';

/**
 * Create a new collection yaml. Delegates to `scripts/create-collection`.
 */
export const POST: APIRoute = async ({ request }) => {
  const body = await request.json().catch(() => ({}));
  const { name, title, description, keywords, location, rating, date } = body;

  if (!name || !title) {
    return new Response('missing name or title', { status: 400 });
  }
  if (!/^[a-z0-9-]+$/.test(name)) {
    return new Response('name must be lowercase slug', { status: 400 });
  }

  const args: string[] = [name, '--title', title];
  if (description) args.push('--description', description);
  if (keywords) args.push('--keywords', keywords);
  if (location) args.push('--location', location);
  if (rating) args.push('--rating', rating);
  if (date) args.push('--date', date);

  const create = await runScript('atomic/create-collection', args);
  if (!create.ok) {
    return new Response(create.stderr || create.stdout || 'create failed', {
      status: 500,
    });
  }

  // If filters were supplied, sync to populate photo list.
  if (keywords || location || rating || date) {
    const sync = await runScript('atomic/sync-collection', [name]);
    if (!sync.ok) {
      return new Response(
        `Collection created but sync failed:\n${sync.stderr || sync.stdout}`,
        { status: 500 },
      );
    }
  }

  return new Response(JSON.stringify({ ok: true, name }), {
    headers: { 'content-type': 'application/json' },
  });
};
