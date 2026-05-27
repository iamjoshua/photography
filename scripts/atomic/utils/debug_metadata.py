#!/usr/bin/env python3

import sys
from pathlib import Path

# Import our metadata module
from photo_metadata import get_metadata

try:
    from iptcinfo3 import IPTCInfo
except ImportError:
    IPTCInfo = None

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None
    TAGS = None

def debug_photo(photo_path):
    """Print all available metadata from a photo."""
    print(f"\n{'='*60}")
    print(f"Photo: {photo_path}")
    print(f"{'='*60}\n")

    # First show what get_metadata returns (our public API)
    print("Metadata from get_metadata() API:")
    print("-" * 40)
    metadata = get_metadata(photo_path)
    if metadata:
        print(f"  Keywords: {metadata.keywords}")
        print(f"  Location: {metadata.location}")
        print(f"  Rating: {metadata.rating}")
        print(f"  Date: {metadata.date}")
        print(f"\n  Camera:")
        print(f"    Make: {metadata.camera_make}")
        print(f"    Model: {metadata.camera_model}")
        print(f"    Lens: {metadata.lens_model}")
        print(f"\n  Settings:")
        print(f"    Focal Length: {metadata.focal_length}mm" if metadata.focal_length else "    Focal Length: None")
        print(f"    Aperture: f/{metadata.aperture}" if metadata.aperture else "    Aperture: None")
        print(f"    Shutter: {metadata.shutter_speed}s" if metadata.shutter_speed else "    Shutter: None")
        print(f"    ISO: {metadata.iso}" if metadata.iso else "    ISO: None")
    else:
        print("  Could not read metadata")
    print()

    # IPTC data
    print("IPTC Data:")
    print("-" * 40)
    try:
        info = IPTCInfo(str(photo_path), force=False)

        # Common IPTC fields to check
        fields_to_check = [
            'keywords', 'caption/abstract', 'headline', 'city', 'province/state',
            'country/primary location name', 'object name', 'supplemental category',
            'category', 'special instructions', 'by-line', 'credit', 'source'
        ]

        found_any = False
        for field in fields_to_check:
            try:
                value = info.get(field)
                if value:
                    found_any = True
                    # Decode bytes to string if needed
                    if isinstance(value, bytes):
                        value = value.decode('utf-8', errors='replace')
                    elif isinstance(value, list):
                        value = [v.decode('utf-8', errors='replace') if isinstance(v, bytes) else v for v in value]
                    print(f"  {field}: {value}")
            except:
                pass

        if not found_any:
            print("  No IPTC data found")

        # Also try to access data attribute directly
        if hasattr(info, 'data'):
            print("\n  Raw IPTC data keys:")
            for key in info.data.keys():
                print(f"    {key}")

    except Exception as e:
        print(f"  Error reading IPTC: {e}")

    # EXIF data
    print("\nEXIF Data:")
    print("-" * 40)
    try:
        img = Image.open(photo_path)
        exif = img.getexif()

        if exif:
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                # Only show first 200 chars for long values
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                print(f"  {tag_name} ({tag_id}): {value_str}")
        else:
            print("  No EXIF data found")
    except Exception as e:
        print(f"  Error reading EXIF: {e}")

    # XMP data (embedded in JPG)
    print("\nXMP Data (embedded):")
    print("-" * 40)
    try:
        with open(photo_path, 'rb') as f:
            content = f.read()

            # Look for XMP packet
            xmp_start = content.find(b'<x:xmpmeta')
            xmp_end = content.find(b'</x:xmpmeta>')

            if xmp_start != -1 and xmp_end != -1:
                xmp_data = content[xmp_start:xmp_end + 12].decode('utf-8', errors='replace')

                # Use the proper XMP parser
                import xml.etree.ElementTree as ET

                try:
                    root = ET.fromstring(xmp_data)
                    ns = {
                        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                        'dc': 'http://purl.org/dc/elements/1.1/',
                        'xmp': 'http://ns.adobe.com/xap/1.0/',
                        'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
                    }

                    # Extract keywords
                    subject_bag = root.find('.//dc:subject/rdf:Bag', ns)
                    if subject_bag is not None:
                        keywords = []
                        for li in subject_bag.findall('rdf:li', ns):
                            if li.text and not any(char.isdigit() or char == ',' for char in li.text):
                                keywords.append(li.text.strip())
                        if keywords:
                            print(f"  Keywords: {keywords}")

                    # Extract location
                    city = root.find('.//photoshop:City', ns)
                    if city is not None and city.text:
                        print(f"  Location/City: {city.text}")

                    # Extract rating
                    rating = root.find('.//xmp:Rating', ns)
                    if rating is not None:
                        print(f"  Rating (from XML parse): {rating.text}")

                    # Check for rating in raw XMP data
                    if 'Rating' in xmp_data:
                        print(f"\n  Found 'Rating' in XMP data")
                        import re
                        # Look for xmp:Rating="5" attribute format
                        rating_attr = re.search(r'xmp:Rating="([^"]+)"', xmp_data)
                        if rating_attr:
                            print(f"  Rating (attribute format): {rating_attr.group(1)}")

                        # Look for <xmp:Rating>5</xmp:Rating> tag format
                        rating_tag = re.search(r'<xmp:Rating>([^<]+)</xmp:Rating>', xmp_data)
                        if rating_tag:
                            print(f"  Rating (tag format): {rating_tag.group(1)}")

                        # Show context around Rating
                        rating_pos = xmp_data.find('Rating')
                        if rating_pos != -1:
                            context = xmp_data[max(0, rating_pos-100):rating_pos+100]
                            print(f"\n  Context around 'Rating':")
                            print(f"  ...{context}...")

                except Exception as e:
                    print(f"  Error parsing XMP XML: {e}")
                    print("\n  Raw XMP (first 1000 chars):")
                    print(f"  {xmp_data[:1000]}...")
            else:
                print("  No XMP data found in JPG")
    except Exception as e:
        print(f"  Error reading XMP: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: debug_metadata.py <photo-path>")
        print("\nExample:")
        print("  python3 scripts/utils/debug_metadata.py photos/example.jpg")
        sys.exit(1)

    photo_path = Path(sys.argv[1])

    if not photo_path.exists():
        print(f"Error: File not found: {photo_path}")
        sys.exit(1)

    debug_photo(photo_path)
