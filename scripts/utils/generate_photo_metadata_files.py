#!/usr/bin/env python3

"""
Generate YAML metadata files for all photos.

Recursively scans the photos directory and creates a mirrored structure in
data/photos/ with YAML files containing metadata for each photo.

Usage:
    python3 generate_metadata_files.py [--dry-run]

Options:
    --dry-run    Show what would be created without actually writing files

Example:
    # Preview what files would be created
    python3 generate_metadata_files.py --dry-run

    # Actually generate the YAML files
    python3 generate_metadata_files.py
"""

import sys
import yaml
import shutil
from pathlib import Path

# Import from the same directory
from photo_metadata import get_metadata


def obj_to_dict(obj):
    """
    Recursively convert an object to a dictionary for YAML serialization.

    Args:
        obj: Any object

    Returns:
        Dictionary representation, recursively processing nested objects
    """
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, list):
        return [obj_to_dict(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Recursively convert object attributes to dict
        return {key: obj_to_dict(value) for key, value in obj.__dict__.items()}
    else:
        return obj


def generate_metadata_files(photos_dir, data_dir, dry_run=False):
    """
    Generate YAML metadata files for all photos.

    Args:
        photos_dir: Path to photos directory
        data_dir: Path to data/photos directory (will be created)
        dry_run: If True, only show what would be created

    Returns:
        Dictionary with statistics:
            - created: Number of files created
            - updated: Number of files updated
            - errors: Number of errors
    """
    photos_dir = Path(photos_dir)
    data_dir = Path(data_dir)

    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'}

    stats = {
        'created': 0,
        'errors': 0
    }

    # Find all image files (excluding exports directory)
    photo_files = []
    for ext in image_extensions:
        photo_files.extend(photos_dir.rglob(f'*{ext}'))

    # Filter out exports directory
    photo_files = [p for p in photo_files if 'exports' not in p.parts]

    # Delete existing metadata files before regenerating
    if data_dir.exists():
        print("Deleting existing metadata files...")
        if not dry_run:
            shutil.rmtree(data_dir)
        print()

    print(f"Found {len(photo_files)} photos to process")
    print()

    for photo_path in sorted(photo_files):
        # Get relative path from photos directory
        rel_path = photo_path.relative_to(photos_dir)

        # Create corresponding YAML path in data/photos
        yaml_path = data_dir / rel_path.with_suffix('.yaml')

        # Read metadata
        metadata = get_metadata(photo_path)
        if not metadata:
            print(f"Error: Could not read metadata from {rel_path}")
            stats['errors'] += 1
            continue

        # Convert metadata object to dictionary dynamically
        yaml_data = obj_to_dict(metadata)

        # Override path to be relative to photos directory (not absolute)
        yaml_data['path'] = str(rel_path)

        if dry_run:
            print(f"Create: {yaml_path.relative_to(data_dir.parent)}")
            stats['created'] += 1
        else:
            # Create parent directory if needed
            yaml_path.parent.mkdir(parents=True, exist_ok=True)

            # Write YAML file
            try:
                with open(yaml_path, 'w') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                print(f"Created: {yaml_path.relative_to(data_dir.parent)}")
                stats['created'] += 1

            except Exception as e:
                print(f"Error writing {yaml_path}: {e}")
                stats['errors'] += 1

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate YAML metadata files for all photos')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created without writing files')
    args = parser.parse_args()

    # Get repository root (two levels up from this script)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent

    photos_dir = repo_root / 'photos'
    data_dir = repo_root / 'data' / 'photos'

    # Validate photos directory exists
    if not photos_dir.exists():
        print(f"Error: Photos directory not found: {photos_dir}")
        sys.exit(1)

    # Run generation
    if args.dry_run:
        print("DRY RUN - No files will be created")
        print()

    stats = generate_metadata_files(photos_dir, data_dir, dry_run=args.dry_run)

    # Print summary
    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Created: {stats['created']}")
    print(f"  Errors:  {stats['errors']}")
    print("=" * 60)

    if args.dry_run:
        print()
        print("This was a dry run. Run without --dry-run to actually create files.")


if __name__ == '__main__':
    main()
