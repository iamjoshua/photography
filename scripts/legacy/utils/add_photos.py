#!/usr/bin/env python3

import os
import sys
import yaml
from pathlib import Path

def get_image_files(photo_dir):
    """Get all image files from a directory, sorted by filename."""
    if not os.path.exists(photo_dir):
        return []

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'}
    images = []

    for filename in os.listdir(photo_dir):
        if any(filename.endswith(ext) for ext in image_extensions):
            images.append(filename)

    return sorted(images)

def create_collection_structure(collection_name, photos):
    """Create a new collection structure."""
    # Use first photo as cover if available, with full path
    cover_path = f"{collection_name}/{photos[0]}" if photos else ""

    # Create title from collection name (capitalize words, replace hyphens)
    title = collection_name.replace('-', ' ').title()

    return {
        'title': title,
        'description': '',
        'cover_path': cover_path,
        'photos': []
    }

def load_or_create_collection(collection_file, collection_name, photos):
    """Load existing collection or create a new one."""
    if os.path.exists(collection_file):
        with open(collection_file, 'r') as f:
            collection = yaml.safe_load(f)
            if collection is None:
                collection = create_collection_structure(collection_name, photos)
    else:
        collection = create_collection_structure(collection_name, photos)

    # Ensure photos list exists
    if 'photos' not in collection or collection['photos'] is None:
        collection['photos'] = []

    return collection

def sync_photos_in_collection(collection, collection_name, photo_files):
    """Sync collection with photo files - add new photos and remove deleted ones."""
    # Create set of current photo paths from files
    current_photo_paths = {f"{collection_name}/{photo_file}" for photo_file in photo_files}

    # Check if cover image will be removed
    cover_path = collection.get('cover_path', '')
    cover_removed = cover_path and cover_path not in current_photo_paths

    # Remove photos that no longer exist
    original_count = len(collection['photos'])
    collection['photos'] = [
        photo for photo in collection['photos']
        if photo['path'] in current_photo_paths
    ]
    removed_count = original_count - len(collection['photos'])

    # Get existing photo paths after removal
    existing_paths = {photo['path'] for photo in collection['photos']}

    # Add new photos
    added_count = 0
    for photo_file in photo_files:
        photo_path = f"{collection_name}/{photo_file}"

        if photo_path not in existing_paths:
            collection['photos'].append({
                'path': photo_path,
                'caption': '',
                'alt': ''
            })
            added_count += 1

    # Update cover_path if it was removed or is invalid
    cover_updated = False
    if cover_removed or (cover_path and cover_path not in current_photo_paths):
        if collection['photos']:
            # Set to first photo in the collection
            collection['cover_path'] = collection['photos'][0]['path']
            cover_updated = True
        else:
            # No photos left, clear the cover
            collection['cover_path'] = ''
            cover_updated = True

    return added_count, removed_count, cover_updated

def save_collection(collection_file, collection):
    """Save collection to YAML file."""
    os.makedirs(os.path.dirname(collection_file), exist_ok=True)

    with open(collection_file, 'w') as f:
        yaml.dump(collection, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    if len(sys.argv) != 2:
        print("Usage: add_photos.py <collection-name>")
        sys.exit(1)

    collection_name = sys.argv[1]

    # Get project root (2 levels up from this script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Define paths
    photo_dir = project_root / 'photos' / collection_name
    collection_file = project_root / 'data' / 'collections' / f'{collection_name}.yaml'

    # Get image files
    photo_files = get_image_files(photo_dir)

    # Check if collection file exists
    if not photo_files and not os.path.exists(collection_file):
        print(f"Error: No image files found in {photo_dir} and no existing collection to update")
        sys.exit(1)

    # Load or create collection
    collection = load_or_create_collection(collection_file, collection_name, photo_files)

    # Sync photos (add new, remove deleted)
    added_count, removed_count, cover_updated = sync_photos_in_collection(collection, collection_name, photo_files)

    # Save collection
    save_collection(collection_file, collection)

    # Report results
    total_photos = len(collection['photos'])
    if added_count > 0 or removed_count > 0 or cover_updated:
        if added_count > 0:
            print(f"Added {added_count} new photo(s)")
        if removed_count > 0:
            print(f"Removed {removed_count} photo(s) that no longer exist")
        if cover_updated:
            if collection['cover_path']:
                print(f"Updated cover_path to: {collection['cover_path']}")
            else:
                print(f"Cleared cover_path (no photos remaining)")
        print(f"Total photos in collection: {total_photos}")
    else:
        print(f"No changes needed. Collection is in sync with {total_photos} photos.")

    print(f"Collection file: {collection_file}")

if __name__ == '__main__':
    main()
