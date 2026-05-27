import fs from 'node:fs/promises';
import path from 'node:path';
import { parse as parseYaml } from 'yaml';
import { DATA_PHOTOS_DIR, R2_SMALL_DIR, R2_LARGE_DIR, stripExtension } from './paths';
import { listCollections } from './collections';
import type { Photo } from '../types';

async function walkYaml(dir: string): Promise<string[]> {
  const out: string[] = [];
  async function walk(d: string): Promise<void> {
    let entries;
    try {
      entries = await fs.readdir(d, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) await walk(full);
      else if (e.isFile() && e.name.endsWith('.yaml')) out.push(full);
    }
  }
  await walk(dir);
  return out;
}

async function exists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

export async function listPhotos(): Promise<Photo[]> {
  const [yamlFiles, collections] = await Promise.all([
    walkYaml(DATA_PHOTOS_DIR),
    listCollections(),
  ]);

  const photos = await Promise.all(
    yamlFiles.map(async (file) => {
      const raw = await fs.readFile(file, 'utf8');
      const data = parseYaml(raw) ?? {};
      if (!data.path) return null;

      const id = stripExtension(data.path);
      const webp = `${id}.webp`;
      const [hasSmall, hasLarge] = await Promise.all([
        exists(path.join(R2_SMALL_DIR, webp)),
        exists(path.join(R2_LARGE_DIR, webp)),
      ]);

      const memberOf = collections
        .filter((c) =>
          c.photos.some((p) => stripExtension(p.path) === id),
        )
        .map((c) => c.name);

      const photo: Photo = {
        id,
        path: data.path,
        filename: path.basename(id),
        keywords: data.keywords ?? [],
        location: data.location ?? {
          sublocation: null,
          city: null,
          state: null,
          country: null,
        },
        rating: data.rating ?? null,
        date: data.date ?? null,
        camera_make: data.camera_make ?? null,
        camera_model: data.camera_model ?? null,
        lens_model: data.lens_model ?? null,
        focal_length: data.focal_length ?? null,
        aperture: data.aperture ?? null,
        shutter_speed: data.shutter_speed ?? null,
        iso: data.iso ?? null,
        hasSmall,
        hasLarge,
        collections: memberOf,
      };
      return photo;
    }),
  );

  const filtered = photos.filter((p): p is Photo => p !== null);
  filtered.sort((a, b) => (b.date ?? '').localeCompare(a.date ?? ''));
  return filtered;
}
