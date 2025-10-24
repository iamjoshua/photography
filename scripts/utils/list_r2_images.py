#!/usr/bin/env python3

"""
List all images in Cloudflare R2 bucket.

Reads configuration from .r2config file in the project root.

Setup:
    1. Copy .r2config.example to .r2config
    2. Fill in your Cloudflare R2 credentials

Usage:
    python3 scripts/utils/list_r2_images.py
"""

import os
import sys
import configparser
from pathlib import Path
import boto3
from botocore.client import Config

def load_r2_config():
    """Load R2 configuration from .r2config file."""
    # Find project root (where .r2config should be)
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

def list_all_objects(client, bucket_name, prefix=''):
    """
    List all objects in R2 bucket, handling pagination.

    Args:
        client: Boto3 S3 client
        bucket_name: Name of the R2 bucket
        prefix: Optional prefix to filter objects (e.g., 'photos/')

    Returns:
        List of object dictionaries with 'Key', 'Size', 'LastModified'
    """
    objects = []
    continuation_token = None

    while True:
        # Build request parameters
        params = {
            'Bucket': bucket_name,
            'MaxKeys': 1000
        }

        if prefix:
            params['Prefix'] = prefix

        if continuation_token:
            params['ContinuationToken'] = continuation_token

        # List objects
        response = client.list_objects_v2(**params)

        # Add objects to our list
        if 'Contents' in response:
            objects.extend(response['Contents'])

        # Check if there are more objects to fetch
        if response.get('IsTruncated'):
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    return objects

def main():
    client, bucket_name = get_r2_client()

    print(f"Listing objects in bucket: {bucket_name}")
    print("-" * 80)

    try:
        objects = list_all_objects(client, bucket_name)

        if not objects:
            print("No objects found in bucket")
            return

        # Print summary
        print(f"Found {len(objects)} objects:\n")

        # Print each object
        for obj in objects:
            key = obj['Key']
            size_mb = obj['Size'] / (1024 * 1024)
            modified = obj['LastModified']
            print(f"{key}")
            print(f"  Size: {size_mb:.2f} MB")
            print(f"  Modified: {modified}")
            print()

        # Print totals
        total_size = sum(obj['Size'] for obj in objects)
        total_size_mb = total_size / (1024 * 1024)
        total_size_gb = total_size / (1024 * 1024 * 1024)

        print("-" * 80)
        print(f"Total: {len(objects)} objects, {total_size_gb:.2f} GB ({total_size_mb:.2f} MB)")

    except Exception as e:
        print(f"Error listing objects: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
