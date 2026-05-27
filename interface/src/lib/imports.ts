import fs from 'node:fs/promises';
import path from 'node:path';
import { PHOTOS_DIR } from './paths';

export const IMPORTS_DIR = path.join(PHOTOS_DIR, 'imports');

export interface PendingImport {
  /** Path relative to photos/imports/, e.g. "2026/arizona/foo.jpg" */
  id: string;
  filename: string;
  size: number;
  modifiedMs: number;
}

const IMAGE_RE = /\.(jpe?g|webp|png|tiff?)$/i;

export async function listImports(): Promise<PendingImport[]> {
  const out: PendingImport[] = [];
  async function walk(rel: string): Promise<void> {
    const abs = path.join(IMPORTS_DIR, rel);
    let entries;
    try {
      entries = await fs.readdir(abs, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      if (e.name.startsWith('.')) continue;
      const childRel = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) {
        await walk(childRel);
      } else if (e.isFile() && IMAGE_RE.test(e.name)) {
        const stat = await fs.stat(path.join(abs, e.name));
        out.push({
          id: childRel,
          filename: e.name,
          size: stat.size,
          modifiedMs: stat.mtimeMs,
        });
      }
    }
  }
  await walk('');
  out.sort((a, b) => a.modifiedMs - b.modifiedMs);
  return out;
}
