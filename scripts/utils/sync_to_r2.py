#!/usr/bin/env python3

"""
Sync local photos directory to Cloudflare R2.

Reads configuration from .r2config file in the project root.

This script ensures R2 perfectly mirrors the local directory by:
- Uploading new files that exist locally but not in R2
- Deleting files from R2 that no longer exist locally
- Re-uploading files where local version is newer

Usage:
    # Sync the dev folder (for testing)
    python3 scripts/utils/sync_to_r2.py photos/dev

    # Later: sync entire photos directory
    python3 scripts/utils/sync_to_r2.py photos
"""

import os
import sys
import configparser
from pathlib import Path
from datetime import datetime, timezone
import boto3
from botocore.client import Config

def load_r2_config():
    """Load R2 configuration from .r2config file."""
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    config_path = project_root / '.r2config'

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Setup instructions:", file=sys.stderr)
        print("  1. Copy .r2config.example to .r2config", file=sys.stderr)
        print("  2. Fill in your Cloudflare R2 credentials", file=sys.stderr)
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    if 'r2' not in config:
        print("Error: [r2] section not found in .r2config", file=sys.stderr)
        sys.exit(1)

    required_keys = ['account_id', 'access_key_id', 'secret_access_key', 'bucket_name']
    missing_keys = [key for key in required_keys if key not in config['r2']]

    if missing_keys:
        print(f"Error: Missing required keys in .r2config: {', '.join(missing_keys)}", file=sys.stderr)
        sys.exit(1)

    return config['r2']

def get_r2_client():
    """Create and return an S3 client configured for Cloudflare R2."""
    r2_config = load_r2_config()

    endpoint_url = f'https://{r2_config["account_id"]}.r2.cloudflarestorage.com'

    return boto3.client(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=r2_config['access_key_id'],
        aws_secret_access_key=r2_config['secret_access_key'],
        config=Config(signature_version='s3v4'),
        region_name='auto'
    ), r2_config['bucket_name']

def list_r2_objects(client, bucket_name, prefix=''):
    """
    List all objects in R2 bucket with given prefix, handling pagination.

    Returns:
        Dict mapping object key to object metadata (Size, LastModified)
    """
    objects = {}
    continuation_token = None

    while True:
        params = {
            'Bucket': bucket_name,
            'MaxKeys': 1000
        }

        if prefix:
            params['Prefix'] = prefix

        if continuation_token:
            params['ContinuationToken'] = continuation_token

        response = client.list_objects_v2(**params)

        if 'Contents' in response:
            for obj in response['Contents']:
                objects[obj['Key']] = {
                    'Size': obj['Size'],
                    'LastModified': obj['LastModified']
                }

        if response.get('IsTruncated'):
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    return objects

def get_local_files(directory, base_prefix):
    """
    Get all files in local directory recursively.

    Args:
        directory: Path to directory to scan
        base_prefix: The prefix to prepend to relative paths (e.g., 'photos/dev/')

    Returns:
        Dict mapping R2 key to file metadata (size, mtime)
    """
    directory = Path(directory)

    if not directory.exists():
        print(f"Error: Directory does not exist: {directory}", file=sys.stderr)
        sys.exit(1)

    files = {}

    for file_path in directory.rglob('*'):
        if file_path.is_file() and not file_path.name.startswith('.'):
            # Get path relative to the directory we're scanning
            relative_path = file_path.relative_to(directory)
            # Construct R2 key by combining base prefix with relative path
            r2_key = base_prefix + str(relative_path)

            stat = file_path.stat()

            files[r2_key] = {
                'path': file_path,
                'size': stat.st_size,
                'mtime': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            }

    return files

def upload_file(client, bucket_name, local_path, r2_key):
    """Upload a file to R2."""
    try:
        with open(local_path, 'rb') as f:
            client.put_object(
                Bucket=bucket_name,
                Key=r2_key,
                Body=f
            )
        return True
    except Exception as e:
        print(f"Error uploading {r2_key}: {e}", file=sys.stderr)
        return False

def delete_file(client, bucket_name, r2_key):
    """Delete a file from R2."""
    try:
        client.delete_object(
            Bucket=bucket_name,
            Key=r2_key
        )
        return True
    except Exception as e:
        print(f"Error deleting {r2_key}: {e}", file=sys.stderr)
        return False

def sync_directory(local_dir, r2_prefix=''):
    """
    Sync local directory to R2.

    Args:
        local_dir: Path to local directory to sync (e.g., 'photos')
        r2_prefix: Prefix to use in R2 (empty string means sync contents to bucket root)
    """
    client, bucket_name = get_r2_client()

    # Normalize the directory path
    local_dir = Path(local_dir)

    # If r2_prefix is not specified, default to syncing directory contents to root
    # (i.e., 'photos/' directory contents go to bucket root, not under 'photos/')
    if r2_prefix == '':
        prefix = ''
        print(f"Syncing contents of {local_dir}/ to R2 bucket '{bucket_name}' root")
    else:
        prefix = r2_prefix.rstrip('/') + '/'
        print(f"Syncing {local_dir} to R2 bucket '{bucket_name}' with prefix '{prefix}'")
    print("-" * 80)

    # Get local files
    print("Scanning local files...")
    local_files = get_local_files(local_dir, prefix)
    print(f"Found {len(local_files)} local files")
    if local_files:
        print("Local file keys:")
        for key in list(local_files.keys())[:5]:  # Show first 5
            print(f"  - {key}")
        if len(local_files) > 5:
            print(f"  ... and {len(local_files) - 5} more")

    # Get R2 files
    print("\nListing R2 objects...")
    r2_objects = list_r2_objects(client, bucket_name, prefix)
    print(f"Found {len(r2_objects)} R2 objects with prefix '{prefix}'")
    if r2_objects:
        print("R2 object keys:")
        for key in list(r2_objects.keys())[:5]:  # Show first 5
            print(f"  - {key}")
        if len(r2_objects) > 5:
            print(f"  ... and {len(r2_objects) - 5} more")
    print()

    # Determine what actions to take
    to_upload = []
    to_delete = []

    # Check which local files need to be uploaded
    for local_key, local_meta in local_files.items():
        if local_key not in r2_objects:
            # File doesn't exist in R2
            to_upload.append((local_key, 'new'))
        else:
            # File exists - check if local is newer
            r2_modified = r2_objects[local_key]['LastModified']
            local_modified = local_meta['mtime']

            # Compare timestamps (allowing 1 second tolerance for filesystem differences)
            from datetime import timedelta
            if local_modified > r2_modified + timedelta(seconds=1):
                to_upload.append((local_key, 'updated'))

    # Check which R2 files need to be deleted
    for r2_key in r2_objects:
        if r2_key not in local_files:
            to_delete.append(r2_key)

    # Print summary
    print("Sync Plan:")
    print(f"  Upload: {len(to_upload)} files")
    print(f"  Delete: {len(to_delete)} files")
    print(f"  No change: {len(local_files) - len(to_upload)} files")
    print()

    if not to_upload and not to_delete:
        print("✓ Everything is already in sync!")
        return

    # Execute uploads
    if to_upload:
        print(f"Uploading {len(to_upload)} files...")
        uploaded = 0
        for local_key, reason in to_upload:
            local_meta = local_files[local_key]
            size_mb = local_meta['size'] / (1024 * 1024)

            print(f"  {'↑' if reason == 'new' else '↻'} {local_key} ({size_mb:.2f} MB) [{reason}]")

            if upload_file(client, bucket_name, local_meta['path'], local_key):
                uploaded += 1

        print(f"✓ Uploaded {uploaded}/{len(to_upload)} files")
        print()

    # Execute deletions
    if to_delete:
        print(f"Deleting {len(to_delete)} files...")
        deleted = 0
        for r2_key in to_delete:
            print(f"  ✗ {r2_key}")

            if delete_file(client, bucket_name, r2_key):
                deleted += 1

        print(f"✓ Deleted {deleted}/{len(to_delete)} files")
        print()

    print("-" * 80)
    print("✓ Sync complete!")

def main():
    # Get project root (same as config loading)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    # Determine what to sync
    if len(sys.argv) == 1:
        # No argument: sync entire photos directory
        local_dir = project_root / 'photos'
        r2_prefix = ''
    elif len(sys.argv) == 2:
        # Subdirectory provided: sync photos/<subdir> to <subdir>/ in R2
        subdir = sys.argv[1]
        local_dir = project_root / 'photos' / subdir
        r2_prefix = subdir
    else:
        print("Usage: python3 scripts/utils/sync_to_r2.py [subdirectory]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python3 scripts/utils/sync_to_r2.py          # sync all of photos/", file=sys.stderr)
        print("  python3 scripts/utils/sync_to_r2.py dev      # sync photos/dev/ to dev/", file=sys.stderr)
        print("  python3 scripts/utils/sync_to_r2.py 2025     # sync photos/2025/ to 2025/", file=sys.stderr)
        sys.exit(1)

    try:
        sync_directory(local_dir, r2_prefix)
    except KeyboardInterrupt:
        print("\n\nSync interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError during sync: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
