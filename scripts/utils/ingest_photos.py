#!/usr/bin/env python3

"""
Photo ingestion script - moves photos from exports to organized directories.

Reads metadata from photos in photos/exports/ and moves them to:
    photos/YYYY/location/filename.jpg

Uses metadata to determine:
    - Year from EXIF date
    - Location from XMP City field (Lightroom)

Falls back to:
    - Year: "unknown-year" if no date metadata
    - Location: "unknown-location" if no city metadata
"""

import sys
import shutil
from pathlib import Path

# Import metadata utilities
from photo_metadata import get_metadata


def extract_year_from_date(date_string):
    """
    Extract year from EXIF date string.

    Args:
        date_string: Date from EXIF (e.g., "2025:10:18 22:33:24")

    Returns:
        Year string (e.g., "2025") or None
    """
    if not date_string:
        return None

    # EXIF dates are typically "YYYY:MM:DD HH:MM:SS"
    try:
        year = str(date_string).split(':')[0].split('-')[0]
        if year.isdigit() and len(year) == 4:
            return year
    except (IndexError, AttributeError):
        pass

    return None


def sanitize_location(location):
    """
    Sanitize location string for use as directory name.

    Args:
        location: City/location string

    Returns:
        Sanitized string safe for directory name
    """
    if not location:
        return None

    # Convert to lowercase and replace spaces/special chars with hyphens
    sanitized = location.lower()
    sanitized = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in sanitized)
    sanitized = '-'.join(filter(None, sanitized.split('-')))  # Remove multiple/trailing hyphens

    return sanitized if sanitized else None


def ingest_photo(photo_path, photos_root, dry_run=False):
    """
    Ingest a single photo by moving it to the appropriate year/location directory.

    Args:
        photo_path: Path to the photo in exports folder
        photos_root: Root photos directory (e.g., /path/to/photos)
        dry_run: If True, only print what would happen without moving files

    Returns:
        Tuple of (success: bool, message: str, destination: Path or None, replaced: bool)
    """
    # Read metadata
    metadata = get_metadata(photo_path)
    if not metadata:
        return False, f"Could not read metadata from {photo_path.name}", None, False

    # Determine year
    year = extract_year_from_date(metadata.date)
    if not year:
        year = "unknown-year"

    # Determine location (use location fields to build path)
    if metadata.location:
        # Build path parts: year/state/city or year/city or year/unknown-location
        location_parts = []

        if metadata.location.state:
            location_parts.append(sanitize_location(metadata.location.state))

        if metadata.location.city:
            location_parts.append(sanitize_location(metadata.location.city))

        if location_parts:
            # Build path: photos_root/year/state/city
            dest_dir = photos_root / year
            for part in location_parts:
                dest_dir = dest_dir / part
        else:
            dest_dir = photos_root / year / "unknown-location"
    else:
        dest_dir = photos_root / year / "unknown-location"

    dest_path = dest_dir / photo_path.name

    # Check if destination already exists (will be replaced)
    replaced = dest_path.exists()

    # Create directory and move file
    if dry_run:
        action = "Would replace" if replaced else "Would move to"
        return True, f"{action}: {dest_path.relative_to(photos_root)}", dest_path, replaced
    else:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(photo_path), str(dest_path))
            action = "Replaced" if replaced else "Moved to"
            return True, f"{action}: {dest_path.relative_to(photos_root)}", dest_path, replaced
        except Exception as e:
            return False, f"Error moving file: {e}", None, False


def main():
    """Main entry point for photo ingestion."""
    # Parse arguments
    dry_run = '--dry-run' in sys.argv

    # Get project root (photography directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    photos_root = project_root / "photos"
    exports_dir = photos_root / "exports"

    # Check if exports directory exists
    if not exports_dir.exists():
        print(f"Exports directory not found: {exports_dir}")
        print("Creating it now...")
        exports_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created: {exports_dir}")
        print("\nPlace photos in this directory and run the script again.")
        return 0

    # Find all image files in exports
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'}
    photos = [f for f in exports_dir.iterdir() if f.is_file() and f.suffix in image_extensions]

    if not photos:
        print(f"No photos found in {exports_dir.relative_to(project_root)}")
        return 0

    # Print header
    mode = "DRY RUN - No files will be moved" if dry_run else "INGESTING PHOTOS"
    print(f"\n{'=' * 60}")
    print(f"{mode}")
    print(f"{'=' * 60}")
    print(f"Found {len(photos)} photo(s) in exports/\n")

    # Process each photo
    success_count = 0
    error_count = 0
    replaced_count = 0

    for photo_path in sorted(photos):
        success, message, dest_path, replaced = ingest_photo(photo_path, photos_root, dry_run)

        status = "✓" if success else "✗"
        print(f"{status} {photo_path.name}")
        print(f"  {message}")

        if success:
            success_count += 1
            if replaced:
                replaced_count += 1
        else:
            error_count += 1

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Summary: {success_count} succeeded, {error_count} failed")
    if replaced_count > 0:
        print(f"  ({replaced_count} photo(s) replaced existing files)")

    if dry_run:
        print("\nThis was a dry run. Use without --dry-run to move files.")

    print(f"{'=' * 60}\n")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
