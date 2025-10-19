#!/usr/bin/env python3

import os
import sys
import yaml
from pathlib import Path

def get_relative_photo_path(absolute_path, project_root):
    """Convert absolute path to relative path from photos directory."""
    abs_path = Path(absolute_path).resolve()
    photos_dir = (project_root / 'photos').resolve()

    # Check if the path is within the photos directory
    try:
        relative_path = abs_path.relative_to(photos_dir)
        return str(relative_path)
    except ValueError:
        # Path is not within photos directory
        return None

def load_or_create_collection(collection_file, collection_name):
    """Load existing collection or create a new one."""
    if os.path.exists(collection_file):
        with open(collection_file, 'r') as f:
            collection = yaml.safe_load(f)
            if collection is None:
                collection = create_new_collection(collection_name)
    else:
        collection = create_new_collection(collection_name)

    # Ensure photos list exists
    if 'photos' not in collection or collection['photos'] is None:
        collection['photos'] = []

    return collection

def create_new_collection(collection_name):
    """Create a new collection structure."""
    # Create title from collection name (capitalize words, replace hyphens)
    title = collection_name.replace('-', ' ').title()

    return {
        'title': title,
        'description': '',
        'cover_path': '',
        'photos': []
    }

def add_photo_to_collection(collection, photo_path):
    """Add photo to collection if not already present."""
    # Check if photo already exists
    existing_paths = {photo['path'] for photo in collection['photos']}

    if photo_path in existing_paths:
        return False

    # Add new photo
    collection['photos'].append({
        'path': photo_path,
        'caption': '',
        'alt': ''
    })

    # If this is the first photo, set it as cover
    if len(collection['photos']) == 1:
        collection['cover_path'] = photo_path

    return True

def save_collection(collection_file, collection):
    """Save collection to YAML file."""
    os.makedirs(os.path.dirname(collection_file), exist_ok=True)

    with open(collection_file, 'w') as f:
        yaml.dump(collection, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    if len(sys.argv) < 3:
        print("Usage: add_to_collection.py <collection-name> <photo-path> [photo-path...]")
        sys.exit(1)

    collection_name = sys.argv[1]
    photo_paths_input = sys.argv[2:]

    # Get project root (2 levels up from this script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Load or create collection
    collection_file = project_root / 'data' / 'collections' / f'{collection_name}.yaml'
    collection = load_or_create_collection(collection_file, collection_name)

    # Track results
    added_photos = []
    skipped_photos = []
    errors = []

    # Process each photo
    for photo_path_input in photo_paths_input:
        # Convert to relative path
        relative_path = get_relative_photo_path(photo_path_input, project_root)

        if relative_path is None:
            errors.append(f"{photo_path_input} - not within photos directory")
            continue

        # Check if the photo file exists
        full_photo_path = project_root / 'photos' / relative_path
        if not full_photo_path.exists():
            errors.append(f"{relative_path} - file not found")
            continue

        # Add photo to collection
        added = add_photo_to_collection(collection, relative_path)

        if added:
            added_photos.append(relative_path)
        else:
            skipped_photos.append(relative_path)

    # Save collection if any photos were added
    if added_photos:
        save_collection(collection_file, collection)

    # Report results
    print(f"\n=== Collection '{collection_name}' Update Summary ===")

    if added_photos:
        print(f"\nAdded {len(added_photos)} photo(s):")
        for photo in added_photos:
            print(f"  + {photo}")

    if skipped_photos:
        print(f"\nSkipped {len(skipped_photos)} photo(s) (already in collection):")
        for photo in skipped_photos:
            print(f"  - {photo}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  ! {error}")

    print(f"\nTotal photos in collection: {len(collection['photos'])}")
    print(f"Collection file: {collection_file}")

if __name__ == '__main__':
    main()
