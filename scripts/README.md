# Photography Scripts

Automated tools for managing a photography website portfolio.

## Overview

This repository manages photos and collections for a photography website. Photos are exported from Adobe Lightroom as JPGs with embedded metadata (keywords, ratings, locations), then organized into collections using these scripts.

### How It Works

**Scripts are organized in two layers:**

1. **Bash scripts** (in `scripts/`) - Easy-to-call commands for daily use
   - Simple interface: `./scripts/sync-collection portfolio`
   - No Python knowledge required
   - Just wrapper scripts that call the Python implementations

2. **Python modules** (in `scripts/utils/`) - The actual implementation logic
   - Handle complex operations (YAML parsing, metadata reading, filtering)
   - Reusable across multiple scripts
   - Easier to maintain and test than bash

**Workflow:**
- Tag and rate photos in Lightroom during editing
- Export as JPGs with metadata
- Run scripts to organize them into collections automatically
- Collections are stored as YAML files for website consumption

## Setup

These scripts require Python 3 and several libraries.

### Install dependencies

```bash
pip3 install pyyaml iptcinfo3 Pillow
```

**Library purposes:**
- `pyyaml` - Reading and writing collection YAML files
- `iptcinfo3` - Reading IPTC metadata (keywords, location) from JPG files
- `Pillow` - Reading EXIF metadata (date) from JPG files

## Collection Types

There are two types of collections:

1. **Filtered Collections**: Define filter criteria (keywords, location, rating, etc.) and are automatically populated by the `sync-collection` script based on photo metadata
2. **Manual Collections**: No filters, photos are manually added using `add-to-collection` or `add-photos`

## Scripts

### `generate-photo-metadata-files`

Generates YAML metadata files for all photos in the repository. Creates a mirrored directory structure in `data/photos/` with one YAML file per photo containing all metadata extracted from the image.

**Usage:**
```bash
# Preview what would be created (dry run)
./scripts/generate-photo-metadata-files --dry-run

# Actually generate the YAML files
./scripts/generate-photo-metadata-files
```

**What it does:**
- Recursively scans all photos in `photos/` directory (excluding `exports/`)
- Reads metadata from each photo using the `photo_metadata` module
- Creates corresponding YAML files in `data/photos/` with the same directory structure
- Each YAML file contains all metadata fields dynamically (keywords, location, rating, date, etc.)
- Updates existing YAML files if they already exist
- Future changes to the `PhotoMetadata` class are automatically reflected in output

**Examples:**
```bash
# Preview what files would be created
./scripts/generate-photo-metadata-files --dry-run

# Generate all metadata files
./scripts/generate-photo-metadata-files
```

**Directory structure created:**
```
data/photos/
  2025/
    seattle/
      photo-1.yaml
      photo-2.yaml
    portland/
      photo-3.yaml
```

**Example YAML output:**
```yaml
path: /path/to/photos/2025/seattle/photo-1.jpg
keywords:
- street
- washington
location:
  sublocation: Pike Place Market
  city: Seattle
  state: Washington
  country: USA
rating: 4
date: 2025:10:18 23:19:56
```

**Notes:**
- Dynamically serializes all metadata fields without hardcoding
- Future additions to `PhotoMetadata` or `Location` classes automatically appear in YAML
- Uses `--dry-run` to preview changes before generating files
- Processes all supported image formats (jpg, jpeg, png, gif)

### `ingest-photos`

Processes photos from the exports folder and organizes them into year/location directories based on metadata.

**Usage:**
```bash
# Preview what would happen (dry run)
./scripts/ingest-photos --dry-run

# Actually move the photos
./scripts/ingest-photos
```

**What it does:**
- Scans all photos in `photos/exports/`
- Reads EXIF date to determine year (e.g., "2025")
- Reads IPTC City to determine location (e.g., "seattle")
- Moves photos to `photos/YYYY/location/filename.jpg`
- Creates directories as needed
- Falls back to "unknown-year" or "unknown-location" if metadata is missing
- Replaces existing files if re-exporting edited photos (logs replacements)

**Examples:**
```bash
# First, see what would happen
./scripts/ingest-photos --dry-run

# Then actually move the files
./scripts/ingest-photos
```

**Directory structure created:**
```
photos/
  2025/
    seattle/
      photo-1.jpg
      photo-2.jpg
    portland/
      photo-3.jpg
  2024/
    unknown-location/
      photo-4.jpg
```

**Notes:**
- Location names are sanitized (lowercased, spaces become hyphens)
- If the exports folder doesn't exist, it will be created
- Use `--dry-run` to preview changes before moving files
- Photos are moved (not copied) from exports to their destination
- Requires `Pillow` library for EXIF date reading

### `create-collection`

Creates a new collection file with optional filter criteria.

**Usage:**
```bash
./scripts/create-collection <collection-name> [options]
```

**Options:**
- `--title "Title"` - Display title (defaults to capitalized collection name)
- `--description "Description"` - Collection description
- `--keywords "keyword1, keyword2"` - Comma-separated keywords from photo IPTC metadata
- `--location "Location"` - Location from photo IPTC metadata
- `--rating "4+"` - Minimum star rating (e.g., "3+", "4+", "5")
- `--date "2025"` - Date filter (e.g., "2025", "2025-06", "2025-06-15")

**Examples:**
```bash
# Manual collection (no filters)
./scripts/create-collection my-favorites --title "My Favorites"

# Filtered collection by keywords
./scripts/create-collection street-photography --keywords "street, urban" --location "Seattle" --rating "4+"

# Filtered by date
./scripts/create-collection year-2025 --date "2025"
```

**What it does:**
- Creates `data/collections/<collection-name>.yaml`
- If filters are provided, creates a filtered collection that can be synced with `sync-collection`
- If no filters are provided, creates a manual collection for use with `add-to-collection`
- Will not overwrite existing collections

**Notes:**
- Filtered collections use photo metadata (IPTC keywords, location, rating, date)
- Multiple keywords are OR'd (photo must have at least one)
- All filter criteria are AND'd together
- Run `sync-collection` after creating a filtered collection to populate it

### `sync-collection`

Scans all JPG photos and populates filtered collections based on their metadata criteria.

**Usage:**
```bash
# Sync a single collection
./scripts/sync-collection <collection-name>

# Sync all filtered collections
./scripts/sync-collection --all
```

**Examples:**
```bash
# Sync one collection
./scripts/sync-collection street-photography

# Sync all collections that have filters
./scripts/sync-collection --all
```

**What it does:**
- Scans all JPG files in the `photos/` directory (recursively)
- Reads IPTC and EXIF metadata from each photo
- For each filtered collection, finds photos matching the filter criteria
- Replaces the photos list with current matches (sync mode)
- Updates the cover_path to the first photo if needed
- Skips manual collections (those without a `filters` field)

**Metadata reading:**
- **Keywords**: IPTC Keywords field (set in Lightroom)
- **Location**: IPTC City field (set in Lightroom)
- **Date**: EXIF DateTime/DateTimeOriginal (from photo EXIF)
- **Rating**: Currently not supported (Lightroom typically stores this in XMP)

**Notes:**
- Only works with filtered collections (collections that have a `filters` field)
- Manual collections are skipped automatically
- Uses replace mode: photos list is completely replaced with current matches
- Keywords are case-insensitive and OR'd (photo needs at least one matching keyword)
- All other filter criteria are AND'd together
- Requires `iptcinfo3` and `Pillow` libraries to be installed

### `add-photos`

Adds photos from a directory to a collection file. Creates the collection file if it doesn't exist, or updates it if it does.

**Usage:**
```bash
./scripts/add-photos <collection-name>
```

**Example:**
```bash
./scripts/add-photos wa-state-fair
```

**What it does:**
- Scans `photos/<collection-name>/` for all image files (jpg, jpeg, png, gif)
- Creates or updates `data/collections/<collection-name>.yaml`
- Adds new photos to the collection (skips photos already in the list)
- Preserves existing photos and their captions/alt text
- Can be run multiple times as you add new photos to the directory

**Collection file structure:**
```yaml
title: "Collection Title"
description: ""
cover_path: "first-photo.jpg"
photos:
  - path: "collection-name/photo-1.jpg"
    caption: ""
    alt: ""
  - path: "collection-name/photo-2.jpg"
    caption: ""
    alt: ""
```

**Notes:**
- New collections are created with a default title (capitalized collection name)
- The cover_path is set to the first photo's full path
- Photos are added with empty caption and alt fields for you to fill in later
- Existing photos maintain their original caption/alt values
- If a photo is removed from the directory, it will be removed from the collection
- If the cover photo is removed, the cover_path is automatically updated to the first remaining photo

### `add-to-collection`

Adds one or more photos to any collection (creates the collection if it doesn't exist).

**Usage:**
```bash
./scripts/add-to-collection <collection-name> <absolute-photo-path> [absolute-photo-path...]
```

**Examples:**
```bash
# Single photo
./scripts/add-to-collection street /Users/joshuaheiland/Projects/photography/photos/2025/seattle/street-scene.jpg

# Multiple photos (space-separated)
./scripts/add-to-collection street /path/to/photo1.jpg /path/to/photo2.jpg /path/to/photo3.jpg
```

**What it does:**
- Converts absolute paths to relative paths from the `photos/` directory
- Creates or updates `data/collections/<collection-name>.yaml`
- Adds photos if not already present in the collection
- Skips photos that are already in the collection
- Preserves existing photos and their captions/alt text
- Provides a summary showing which photos were added, skipped, or had errors

**Notes:**
- All photos must be located within the `photos/` directory
- You can drag and drop multiple photo files into the terminal (separated by spaces)
- The script validates that each photo file exists before adding it
- Photos are added with empty caption and alt fields for you to fill in later
- New collections are created with a default title (capitalized collection name)
- The cover_path is set to the first photo added
- The collection is only saved if at least one photo was successfully added

### `add-collection-from-exports`

Quickly build a collection from photos exported from Lightroom. This script intelligently handles photos that are already ingested vs. new photos, avoiding duplication while keeping version control clean.

**Usage:**
```bash
# Export collection from Lightroom to photos/exports/
./scripts/add-collection-from-exports <collection-name>
```

**Examples:**
```bash
# Export a curated set from Lightroom, then add to collection
./scripts/add-collection-from-exports my-favorites

# Build a new collection from fresh exports
./scripts/add-collection-from-exports client-portfolio
```

**What it does:**
- Scans all photos in `photos/exports/`
- For each photo:
  - Checks if photo already exists in the `photos/` directory (using ingestion logic to determine expected location)
  - **If already ingested**: Adds to collection and deletes from exports (avoids duplication)
  - **If not yet ingested**: Ingests photo first (moves to proper year/location directory), then adds to collection
- Creates collection if it doesn't exist (manual collection, no filters)
- Updates existing collection if it already exists

**Workflow:**
1. Select photos in Lightroom (e.g., a curated collection)
2. Export to `photos/exports/` directory
3. Run this script with your desired collection name
4. Photos are organized and added to collection automatically


### `add-to-portfolio`

Convenience script that adds photos to your portfolio collection. This is a wrapper around `add-to-collection` with the collection name set to "portfolio".

**Usage:**
```bash
./scripts/add-to-portfolio <absolute-photo-path> [absolute-photo-path...]
```

**Examples:**
```bash
# Single photo
./scripts/add-to-portfolio /Users/joshuaheiland/Projects/photography/photos/2025/northern-cascades/amazing-shot.jpg

# Multiple photos (space-separated)
./scripts/add-to-portfolio /path/to/photo1.jpg /path/to/photo2.jpg /path/to/photo3.jpg
```

**What it does:**
- Same as `add-to-collection` but automatically uses the "portfolio" collection
- See `add-to-collection` for full details
