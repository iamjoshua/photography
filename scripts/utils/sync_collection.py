#!/usr/bin/env python3

import os
import sys
import yaml
from pathlib import Path

# Import photo metadata utilities
from photo_metadata import get_metadata, matches_filters


def scan_photos(project_root, filters):
    """Scan all photos in the photos directory and return matching paths."""
    photos_dir = project_root / 'photos'
    matching_photos = []

    if not photos_dir.exists():
        return matching_photos

    # Get all JPG files (exported from Lightroom)
    image_extensions = {'.jpg', '.jpeg', '.JPG', '.JPEG'}

    for photo_path in photos_dir.rglob('*'):
        if photo_path.is_file() and photo_path.suffix in image_extensions:
            # Read metadata
            metadata = get_metadata(photo_path)

            # Check if matches filters
            if matches_filters(metadata, filters):
                # Convert to relative path from photos directory
                relative_path = photo_path.relative_to(photos_dir)
                matching_photos.append(str(relative_path))

    return sorted(matching_photos)


def load_collection(collection_file):
    """Load collection from YAML file."""
    if not os.path.exists(collection_file):
        print(f"Error: Collection file not found at {collection_file}")
        sys.exit(1)

    with open(collection_file, 'r') as f:
        collection = yaml.safe_load(f)
        if collection is None:
            print(f"Error: Invalid collection file")
            sys.exit(1)

    return collection


def save_collection(collection_file, collection):
    """Save collection to YAML file."""
    with open(collection_file, 'w') as f:
        yaml.dump(collection, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def sync_single_collection(collection_file, project_root):
    """Sync a single collection."""
    collection = load_collection(collection_file)
    collection_name = collection_file.stem

    # Check if this is a filtered collection
    if 'filters' not in collection or not collection['filters']:
        print(f"Skipping '{collection_name}' (manual collection, no filters)")
        return False

    filters = collection['filters']

    # Scan photos
    print(f"Scanning photos for collection '{collection_name}'...")
    matching_photos = scan_photos(project_root, filters)

    # Update collection
    old_count = len(collection.get('photos', []))
    collection['photos'] = [
        {'path': photo, 'caption': '', 'alt': ''}
        for photo in matching_photos
    ]

    # Update cover if needed
    if matching_photos and not collection.get('cover_path'):
        collection['cover_path'] = matching_photos[0]
    elif not matching_photos:
        collection['cover_path'] = ''

    # Save collection
    save_collection(collection_file, collection)

    # Report
    new_count = len(matching_photos)
    print(f"  Before: {old_count} photos")
    print(f"  After: {new_count} photos")
    print(f"  Change: {new_count - old_count:+d}")

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: sync_collection.py <collection-name> | --all")
        sys.exit(1)

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    collections_dir = project_root / 'data' / 'collections'

    # Sync all or single collection
    if sys.argv[1] == '--all':
        print("\n=== Syncing All Filtered Collections ===\n")

        synced_count = 0
        skipped_count = 0

        for collection_file in sorted(collections_dir.glob('*.yaml')):
            if sync_single_collection(collection_file, project_root):
                synced_count += 1
            else:
                skipped_count += 1
            print()

        print(f"=== Summary ===")
        print(f"Synced: {synced_count} collections")
        print(f"Skipped: {skipped_count} collections (manual)")

    else:
        collection_name = sys.argv[1]
        collection_file = collections_dir / f'{collection_name}.yaml'

        print(f"\n=== Syncing Collection '{collection_name}' ===\n")
        sync_single_collection(collection_file, project_root)


if __name__ == '__main__':
    main()
