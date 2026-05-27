import type { APIRoute } from 'astro';
import { listCollections } from '../../../lib/collections';

/**
 * Lightweight list of collections for client-side menus. Returns just
 * the fields the UI needs — name (slug) and title.
 */
export const GET: APIRoute = async () => {
  const all = await listCollections();
  const out = all.map((c) => ({ name: c.name, title: c.title }));
  return new Response(JSON.stringify(out), {
    headers: { 'content-type': 'application/json' },
  });
};
