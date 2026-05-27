import fs from 'node:fs';
import path from 'node:path';

function findRepoRoot(): string {
  let dir = process.cwd();
  while (dir !== path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, 'data', 'photography.yaml'))) {
      return dir;
    }
    dir = path.dirname(dir);
  }
  throw new Error('Could not locate photography repo root from ' + process.cwd());
}

export const REPO_ROOT = findRepoRoot();
export const DATA_DIR = path.join(REPO_ROOT, 'data');
export const DATA_PHOTOS_DIR = path.join(DATA_DIR, 'photos');
export const DATA_COLLECTIONS_DIR = path.join(DATA_DIR, 'collections');
export const PHOTOS_DIR = path.join(REPO_ROOT, 'photos');
export const R2_DIR = path.join(REPO_ROOT, 'r2');
export const R2_SMALL_DIR = path.join(R2_DIR, 'small');
export const R2_LARGE_DIR = path.join(R2_DIR, 'large');
export const SCRIPTS_DIR = path.join(REPO_ROOT, 'scripts');

export function stripExtension(p: string): string {
  return p.replace(/\.[^.]+$/, '');
}
