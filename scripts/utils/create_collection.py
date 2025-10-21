#!/usr/bin/env python3

import os
import sys
import yaml
import argparse
from pathlib import Path

def parse_filters(args):
    """Parse filter arguments into a filters dictionary."""
    filters = {}

    if args.keywords:
        filters['keywords'] = args.keywords

    if args.location:
        filters['location'] = args.location

    if args.rating:
        filters['rating'] = args.rating

    if args.date:
        filters['date'] = args.date

    return filters if filters else None

def create_collection_structure(collection_name, title, description, filters):
    """Create a new collection structure."""
    # Use provided title or generate from collection name
    if not title:
        title = collection_name.replace('-', ' ').title()

    collection = {
        'title': title,
        'description': description or '',
        'cover_path': ''
    }

    # Add filters if provided (filtered collection)
    if filters:
        collection['filters'] = filters

    # Add empty photos list
    collection['photos'] = []

    return collection

def save_collection(collection_file, collection):
    """Save collection to YAML file."""
    os.makedirs(os.path.dirname(collection_file), exist_ok=True)

    with open(collection_file, 'w') as f:
        yaml.dump(collection, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    parser = argparse.ArgumentParser(
        description='Create a new photo collection with optional filters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Manual collection (no filters)
  %(prog)s my-favorites --title "My Favorites"

  # Filtered collection
  %(prog)s street-photography --keywords "street, urban" --location "Seattle" --rating "4+"

  # Filtered by date
  %(prog)s year-2025 --date "2025"
        """
    )

    parser.add_argument('collection_name', help='Name of the collection (used for filename)')
    parser.add_argument('--title', help='Display title for the collection (defaults to capitalized collection name)')
    parser.add_argument('--description', default='', help='Description of the collection')

    # Filter options
    parser.add_argument('--keywords', help='Comma-separated keywords to filter by (e.g., "street, urban")')
    parser.add_argument('--location', help='Location to filter by (e.g., "Seattle")')
    parser.add_argument('--rating', help='Minimum rating to filter by (e.g., "4+", "5")')
    parser.add_argument('--date', help='Date to filter by (e.g., "2025", "2025-06")')

    args = parser.parse_args()

    # Get project root (2 levels up from this script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Define collection file path
    collection_file = project_root / 'data' / 'collections' / f'{args.collection_name}.yaml'

    # Check if collection already exists
    if collection_file.exists():
        print(f"Error: Collection already exists at {collection_file}")
        print(f"To update filters, edit the YAML file directly and run sync-collection")
        sys.exit(1)

    # Parse filters
    filters = parse_filters(args)

    # Create collection structure
    collection = create_collection_structure(
        args.collection_name,
        args.title,
        args.description,
        filters
    )

    # Save collection
    save_collection(collection_file, collection)

    # Report results
    print(f"\n=== Collection Created ===")
    print(f"\nCollection: {args.collection_name}")
    print(f"Title: {collection['title']}")
    if collection['description']:
        print(f"Description: {collection['description']}")

    if filters:
        print(f"\nFilters:")
        for key, value in filters.items():
            print(f"  {key}: {value}")
        print(f"\nThis is a filtered collection. Run './scripts/sync-collection {args.collection_name}' to populate it with matching photos.")
    else:
        print(f"\nThis is a manual collection. Use './scripts/add-to-collection {args.collection_name} <photo-paths>' to add photos.")

    print(f"\nCollection file: {collection_file}")

if __name__ == '__main__':
    main()
