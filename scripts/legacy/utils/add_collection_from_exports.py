#!/usr/bin/env python3

"""
Add photos from exports directory to a collection.

Workflow:
1. Export collection from Lightroom to photos/exports/
2. Run this script with collection name
3. For each photo:
   - Check if already exists in photos/ directory (using ingestion logic)
   - If exists: just add to collection, delete from exports
   - If doesn't exist: ingest it, then add to collection
4. Collection is created if it doesn't exist (manual collection only)

This allows building arbitrary collections from Lightroom without duplicating photos.
"""

import sys
from pathlib import Path

# Import utilities - reuse existing functions to avoid duplication
from ingest_photos import ingest_photo
from add_to_collection import load_or_create_collection, add_photo_to_collection, save_collection


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: add_collection_from_exports.py <collection-name>")
        print("\nExports photos from photos/exports/ to a collection.")
        print("Photos already in the photos/ directory are added to the collection and deleted from exports.")
        print("Photos not yet ingested are first ingested, then added to the collection.")
        sys.exit(1)

    collection_name = sys.argv[1]

    # Get paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    photos_root = project_root / "photos"
    exports_dir = photos_root / "exports"
    collections_dir = project_root / "data" / "collections"
    collection_file = collections_dir / f"{collection_name}.yaml"

    # Check exports directory
    if not exports_dir.exists():
        print(f"Error: Exports directory not found: {exports_dir}")
        sys.exit(1)

    # Find photos in exports
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'}
    photos = [f for f in exports_dir.iterdir() if f.is_file() and f.suffix in image_extensions]

    if not photos:
        print(f"No photos found in {exports_dir.relative_to(project_root)}")
        sys.exit(0)

    # Load or create collection
    collection = load_or_create_collection(collection_file, collection_name)

    # Print header
    print(f"\n{'=' * 60}")
    print(f"Adding photos to collection '{collection_name}'")
    print(f"{'=' * 60}")
    print(f"Found {len(photos)} photo(s) in exports/\n")

    # Process each photo
    already_existed = []
    ingested = []
    added_count = 0
    already_in_collection = []
    errors = []

    for photo_path in sorted(photos):
        print(f"Processing {photo_path.name}...")

        # Use dry_run to check where photo would be ingested and if it already exists
        success, message, dest_path, replaced = ingest_photo(photo_path, photos_root, dry_run=True)

        if not success or not dest_path:
            print(f"  ✗ Could not determine destination: {message}")
            errors.append(photo_path.name)
            continue

        relative_path = str(dest_path.relative_to(photos_root))

        if replaced:
            # Photo already exists - just add to collection and delete from exports
            if add_photo_to_collection(collection, relative_path):
                print(f"  ✓ Already ingested at {relative_path}")
                print(f"    Added to collection")
                added_count += 1
                already_existed.append(photo_path.name)
            else:
                print(f"  → Already in collection at {relative_path}")
                already_in_collection.append(relative_path)

            # Delete from exports (photo already exists in photos/)
            try:
                photo_path.unlink()
                print(f"    Deleted from exports/")
            except Exception as e:
                print(f"    Warning: Could not delete from exports: {e}")
        else:
            # Photo doesn't exist - ingest it for real
            success, message, dest_path, replaced = ingest_photo(photo_path, photos_root, dry_run=False)

            if success and dest_path:
                relative_path = str(dest_path.relative_to(photos_root))
                print(f"  ✓ {message}")
                ingested.append(relative_path)

                # Add to collection
                if add_photo_to_collection(collection, relative_path):
                    print(f"    Added to collection")
                    added_count += 1
                else:
                    print(f"    Already in collection")
                    already_in_collection.append(relative_path)
            else:
                print(f"  ✗ {message}")
                errors.append(photo_path.name)

    # Save collection if anything was added
    if added_count > 0:
        save_collection(collection_file, collection)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Already existed: {len(already_existed)} (deleted from exports)")
    print(f"  Newly ingested: {len(ingested)}")
    print(f"  Added to collection: {added_count}")
    print(f"  Already in collection: {len(already_in_collection)}")
    if errors:
        print(f"  Errors: {len(errors)}")

    if added_count > 0:
        print(f"\nCollection updated: {collection_file}")
        print(f"Total photos in collection: {len(collection.get('photos', []))}")
    elif already_in_collection:
        print(f"\nNo new photos added (all already in collection)")

    print(f"{'=' * 60}\n")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
