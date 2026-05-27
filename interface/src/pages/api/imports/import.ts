import type { APIRoute } from 'astro';
import { streamScript } from '../../../lib/runScript';

/**
 * Ingest every file currently in photos/imports/. Streams the script's
 * stdout/stderr so the client can show step-by-step progress.
 *
 * Body: { collection: string | null }
 *   - null/empty: catalog only (no collection)
 *   - string:     also add every ingested photo to that collection
 *
 * Response: chunked text/plain. The script's raw output, followed by a
 * sentinel line `__DONE__:<exitCode>`.
 *
 * Delegates to `scripts/workflows/ingest-and-sync [--collection NAME]`.
 */
export const POST: APIRoute = async ({ request }) => {
  const body = await request.json().catch(() => ({}));
  const collection = body?.collection;

  const args: string[] = [];
  if (typeof collection === 'string' && collection) {
    args.push('--collection', collection);
  }

  return streamScript('workflows/ingest-and-sync', args);
};
