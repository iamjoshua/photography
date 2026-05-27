import type { APIRoute } from 'astro';
import fs from 'node:fs/promises';
import path from 'node:path';
import { R2_SMALL_DIR, R2_LARGE_DIR } from '../../../lib/paths';
import { IMPORTS_DIR } from '../../../lib/imports';

/**
 * Serves local images:
 *   /api/img/small/<path>.webp   ← r2/small/
 *   /api/img/large/<path>.webp   ← r2/large/
 *   /api/img/import/<path>       ← photos/imports/ (raw, original format)
 */
export const GET: APIRoute = async ({ params }) => {
  const raw = (params.path as string | undefined) ?? '';
  const [size, ...rest] = raw.split('/');

  let base: string;
  let contentType: string;
  switch (size) {
    case 'small':
      base = R2_SMALL_DIR;
      contentType = 'image/webp';
      break;
    case 'large':
      base = R2_LARGE_DIR;
      contentType = 'image/webp';
      break;
    case 'import':
      base = IMPORTS_DIR;
      contentType = guessContentType(rest.join('/'));
      break;
    default:
      return new Response('not found', { status: 404 });
  }

  const rel = rest.join('/');
  const full = path.resolve(base, rel);
  if (!full.startsWith(base + path.sep)) {
    return new Response('forbidden', { status: 403 });
  }

  try {
    const buf = await fs.readFile(full);
    return new Response(buf, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'no-cache',
      },
    });
  } catch {
    return new Response('not found', { status: 404 });
  }
};

function guessContentType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'jpg':
    case 'jpeg':
      return 'image/jpeg';
    case 'png':
      return 'image/png';
    case 'webp':
      return 'image/webp';
    case 'tif':
    case 'tiff':
      return 'image/tiff';
    default:
      return 'application/octet-stream';
  }
}
