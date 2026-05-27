#!/usr/bin/env python3

"""
Generate small + large webp variants for every photo under photos/.

Writes to:
    r2/small/<same relative path>/foo.webp  (longest side 800)
    r2/large/<same relative path>/foo.webp  (longest side 2400)

Quality 100. Preserves ICC color profile. Applies EXIF orientation.
Resizes by longest side so landscape and portrait produce similar pixel counts.
Does not upscale: if source longest side is smaller than target, keeps source size.

Skips photos/imports/ (Lightroom drop) and photos/dev/.

Local only — does not upload to R2.

Usage:
    python3 scripts/utils/build_r2.py
"""

import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image, ImageFilter, ImageOps

SIZES = {
    'small': 800,
    'large': 2400,
}

QUALITY = 100
UNSHARP = ImageFilter.UnsharpMask(radius=1, percent=100, threshold=2)
SKIP_DIRS = {'imports', 'dev'}
JPG_SUFFIXES = {'.jpg', '.jpeg'}


def generate_one(src_str: str, photos_root_str: str, r2_root_str: str) -> tuple[str, str]:
    src = Path(src_str)
    photos_root = Path(photos_root_str)
    r2_root = Path(r2_root_str)
    rel = src.relative_to(photos_root)
    rel_webp = rel.with_suffix('.webp')
    try:
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)
            icc_profile = img.info.get('icc_profile')
            for variant_name, target_size in SIZES.items():
                out_path = r2_root / variant_name / rel_webp
                out_path.parent.mkdir(parents=True, exist_ok=True)
                longest = max(img.width, img.height)
                if longest <= target_size:
                    resized = img
                else:
                    scale = target_size / longest
                    new_w = round(img.width * scale)
                    new_h = round(img.height * scale)
                    resized = img.resize((new_w, new_h), Image.LANCZOS)
                    resized = resized.filter(UNSHARP)
                save_kwargs = {'quality': QUALITY, 'method': 6}
                if icc_profile:
                    save_kwargs['icc_profile'] = icc_profile
                resized.save(out_path, 'WEBP', **save_kwargs)
        return (str(rel), 'ok')
    except Exception as e:
        return (str(rel), f'error: {e}')


def collect_sources(photos_root: Path) -> list[Path]:
    sources: list[Path] = []
    for p in photos_root.rglob('*'):
        if not p.is_file():
            continue
        if p.suffix.lower() not in JPG_SUFFIXES:
            continue
        rel_parts = p.relative_to(photos_root).parts
        if rel_parts and rel_parts[0] in SKIP_DIRS:
            continue
        sources.append(p)
    return sorted(sources)


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    photos_root = repo_root / 'photos'
    r2_root = repo_root / 'r2'

    if not photos_root.exists():
        print(f"Error: {photos_root} not found", file=sys.stderr)
        sys.exit(1)

    sources = collect_sources(photos_root)
    print(f"Found {len(sources)} photos")
    print(f"Generating {', '.join(SIZES.keys())} variants → {r2_root}/")
    print("-" * 80)

    ok = 0
    failed = 0
    with ProcessPoolExecutor() as ex:
        futures = {
            ex.submit(generate_one, str(p), str(photos_root), str(r2_root)): p
            for p in sources
        }
        for i, fut in enumerate(as_completed(futures), start=1):
            rel, status = fut.result()
            if status == 'ok':
                ok += 1
                print(f"  [{i}/{len(sources)}] ✓ {rel}")
            else:
                failed += 1
                print(f"  [{i}/{len(sources)}] ✗ {rel}  {status}", file=sys.stderr)

    print("-" * 80)
    print(f"Generated: {ok}")
    if failed:
        print(f"Failed: {failed}")


if __name__ == '__main__':
    main()
