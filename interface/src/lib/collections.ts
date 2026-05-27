import fs from 'node:fs/promises';
import path from 'node:path';
import { parse as parseYaml } from 'yaml';
import { DATA_COLLECTIONS_DIR } from './paths';
import type { Collection } from '../types';

export async function listCollections(): Promise<Collection[]> {
  let entries: string[];
  try {
    entries = await fs.readdir(DATA_COLLECTIONS_DIR);
  } catch {
    return [];
  }

  const out: Collection[] = [];
  for (const entry of entries) {
    if (!entry.endsWith('.yaml')) continue;
    const raw = await fs.readFile(path.join(DATA_COLLECTIONS_DIR, entry), 'utf8');
    const data = parseYaml(raw) ?? {};
    out.push({
      name: entry.replace(/\.yaml$/, ''),
      title: data.title ?? '',
      description: data.description ?? '',
      cover_path: data.cover_path ?? '',
      filters: data.filters,
      photos: data.photos ?? [],
    });
  }

  out.sort((a, b) => (a.title || a.name).localeCompare(b.title || b.name));
  return out;
}

export async function getCollection(name: string): Promise<Collection | null> {
  const all = await listCollections();
  return all.find((c) => c.name === name) ?? null;
}
