#!/usr/bin/env python3

"""
Cascade-delete a photo from the entire portfolio.

Removes:
- The source jpg in photos/<path>
- The metadata yaml in data/photos/<path-with-yaml-suffix>
- The small + large webp variants in r2/{small,large}/<path-with-webp-suffix>
- Every reference to <path> in every collection yaml in data/collections/
  (entries in `photos:` and `cover_path:` if it matched; cover falls back
  to the first remaining photo, else empty string)

Idempotent: missing pieces are skipped, not errors.

Usage:
    python3 scripts/utils/delete_photo.py <photo-path>

Where <photo-path> is the path relative to photos/, e.g.
"2025/washington/puyallup/Puyallup-Washington-835.jpg".
"""

import sys
import yaml
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/utils/delete_photo.py <photo-path>", file=sys.stderr)
        sys.exit(1)

    photo_path = sys.argv[1].strip().lstrip('/')
    if not photo_path:
        print("Error: empty photo path", file=sys.stderr)
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    photos_root = project_root / 'photos'
    data_photos_root = project_root / 'data' / 'photos'
    r2_root = project_root / 'r2'
    collections_root = project_root / 'data' / 'collections'

    rel = Path(photo_path)
    rel_yaml = rel.with_suffix('.yaml')
    rel_webp = rel.with_suffix('.webp')

    removed = []
    skipped = []

    targets = [
        photos_root / rel,
        data_photos_root / rel_yaml,
        r2_root / 'small' / rel_webp,
        r2_root / 'large' / rel_webp,
    ]
    for t in targets:
        rel_label = t.relative_to(project_root)
        if t.exists():
            t.unlink()
            removed.append(str(rel_label))
        else:
            skipped.append(str(rel_label))

    collections_updated = []
    for col_file in sorted(collections_root.glob('*.yaml')):
        with open(col_file) as f:
            col = yaml.safe_load(f) or {}

        changed = False
        photos_list = col.get('photos') or []
        new_photos = [p for p in photos_list if (p or {}).get('path') != photo_path]
        if len(new_photos) != len(photos_list):
            col['photos'] = new_photos
            changed = True

        if col.get('cover_path') == photo_path:
            col['cover_path'] = (new_photos[0]['path'] if new_photos else '')
            changed = True

        if changed:
            with open(col_file, 'w') as f:
                yaml.dump(col, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            collections_updated.append(col_file.stem)

    print(f"=== Deleted '{photo_path}' ===")
    if removed:
        print("Removed:")
        for r in removed:
            print(f"  ✓ {r}")
    if skipped:
        print("Already missing:")
        for s in skipped:
            print(f"  - {s}")
    if collections_updated:
        print(f"Collections updated: {', '.join(collections_updated)}")
    else:
        print("No collections referenced this photo.")


if __name__ == '__main__':
    main()
