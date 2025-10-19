# Photography Scripts

Utility scripts for managing photo collections.

## Setup

These scripts require Python 3 and the `pyyaml` library.

### Install dependencies

```bash
pip3 install pyyaml
```

## Scripts

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
