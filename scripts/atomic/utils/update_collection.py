#!/usr/bin/env python3

"""
Patch a collection's title and/or description without touching its
photos list or cover_path.

Usage:
    python3 scripts/utils/update_collection.py <collection-name> [--title T] [--description D]
"""

import sys
import yaml
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Update a collection's title and/or description."
    )
    parser.add_argument('collection_name', help='Name of the collection (yaml file basename)')
    parser.add_argument('--title', help='New title')
    parser.add_argument('--description', help='New description')

    args = parser.parse_args()

    if args.title is None and args.description is None:
        print("Error: provide at least one of --title or --description", file=sys.stderr)
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    col_file = project_root / 'data' / 'collections' / f'{args.collection_name}.yaml'

    if not col_file.exists():
        print(f"Error: collection '{args.collection_name}' not found at {col_file}", file=sys.stderr)
        sys.exit(1)

    with open(col_file) as f:
        col = yaml.safe_load(f) or {}

    if args.title is not None:
        col['title'] = args.title
    if args.description is not None:
        col['description'] = args.description

    with open(col_file, 'w') as f:
        yaml.dump(col, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Updated collection '{args.collection_name}'.")
    if args.title is not None:
        print(f"  title: {args.title}")
    if args.description is not None:
        print(f"  description: {args.description}")


if __name__ == '__main__':
    main()
