#!/usr/bin/env python3

"""
Remove a photo from a single collection's yaml.

The photo itself stays in the portfolio. Only the collection reference
is removed. If the photo was the collection's cover, cover_path falls
back to the first remaining photo (or empty string if none).

Idempotent: if the photo isn't in the collection, exits successfully
without making changes.

Usage:
    python3 scripts/utils/remove_from_collection.py <collection-name> <photo-path>
"""

import sys
import yaml
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/utils/remove_from_collection.py <collection-name> <photo-path>", file=sys.stderr)
        sys.exit(1)

    collection_name = sys.argv[1].strip()
    photo_path = sys.argv[2].strip().lstrip('/')

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    col_file = project_root / 'data' / 'collections' / f'{collection_name}.yaml'

    if not col_file.exists():
        print(f"Error: collection '{collection_name}' not found at {col_file}", file=sys.stderr)
        sys.exit(1)

    with open(col_file) as f:
        col = yaml.safe_load(f) or {}

    photos_list = col.get('photos') or []
    new_photos = [p for p in photos_list if (p or {}).get('path') != photo_path]

    changed_photos = len(new_photos) != len(photos_list)
    changed_cover = col.get('cover_path') == photo_path

    if not changed_photos and not changed_cover:
        print(f"Photo '{photo_path}' is not in collection '{collection_name}'. No changes.")
        return

    col['photos'] = new_photos
    if changed_cover:
        col['cover_path'] = new_photos[0]['path'] if new_photos else ''

    with open(col_file, 'w') as f:
        yaml.dump(col, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Removed '{photo_path}' from collection '{collection_name}'.")
    print(f"Photos remaining: {len(new_photos)}")


if __name__ == '__main__':
    main()
