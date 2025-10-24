#!/usr/bin/env python3

"""
Photo metadata reading utilities for Lightroom-exported JPGs.

Public API:
    get_metadata(photo_path) -> PhotoMetadata
        Returns all available metadata from a photo.

    matches_filters(metadata, filters) -> bool
        Check if metadata matches filter criteria.

    Location - Structured location data (city, state, country)
    PhotoMetadata - Container for all photo metadata

Example:
    from photo_metadata import get_metadata, matches_filters

    metadata = get_metadata("photo.jpg")
    print(metadata.keywords)  # ['street', 'seattle']
    print(metadata.rating)    # 4
    print(metadata.location.city)  # 'Seattle'
    print(metadata.location.state)  # 'Washington'
    print(metadata.location.to_path_string())  # 'washington/seattle'

    filters = {'keywords': 'street', 'rating': '4+'}
    if matches_filters(metadata, filters):
        print("Photo matches!")
"""

from pathlib import Path

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None
    TAGS = None


class Location:
    """
    Location metadata container.

    Attributes:
        sublocation: Sublocation/venue name or None (most specific)
        city: City name or None
        state: State/Province name or None
        country: Country name or None
    """
    def __init__(self, sublocation=None, city=None, state=None, country=None):
        self.sublocation = sublocation
        self.city = city
        self.state = state
        self.country = country

    def __repr__(self):
        return f"Location(sublocation={self.sublocation}, city={self.city}, state={self.state}, country={self.country})"

    def __bool__(self):
        """Return True if any location field is set."""
        return bool(self.sublocation or self.city or self.state or self.country)

    def to_path_string(self):
        """
        Convert location to a filesystem-safe path string.

        Returns:
            String like "state/city/sublocation", "state/city", "city", or None

        Examples:
            Location(city="Seattle", state="Washington") -> "washington/seattle"
            Location(city="Seattle", sublocation="Pike Place") -> "seattle/pike-place"
            Location(sublocation="Pike Place", city="Seattle", state="Washington") -> "washington/seattle/pike-place"
            Location(city="Seattle") -> "seattle"
            Location() -> None
        """
        parts = []
        if self.state:
            parts.append(self.state.lower())
        if self.city:
            parts.append(self.city.lower())
        if self.sublocation:
            parts.append(self.sublocation.lower())

        return '/'.join(parts) if parts else None


class PhotoMetadata:
    """
    Photo metadata container.

    Attributes:
        path: Path to the photo file
        keywords: List of keyword strings (lowercase)
        location: Location object with city, state, country or None
        rating: Star rating (1-5) or None
        date: Date string (e.g., "2025:10:18 22:33:24") or None
        camera_make: Camera manufacturer (e.g., "SONY") or None
        camera_model: Camera model (e.g., "ILCE-7CM2") or None
        lens_model: Lens model or None
        focal_length: Focal length in mm (e.g., "50.0") or None
        aperture: F-stop value (e.g., "2.8") or None
        shutter_speed: Exposure time (e.g., "1/125") or None
        iso: ISO speed (e.g., "400") or None
    """
    def __init__(self, path):
        self.path = path
        self.keywords = []
        self.location = None
        self.rating = None
        self.date = None
        self.camera_make = None
        self.camera_model = None
        self.lens_model = None
        self.focal_length = None
        self.aperture = None
        self.shutter_speed = None
        self.iso = None

    def __repr__(self):
        return f"PhotoMetadata(path={self.path}, keywords={self.keywords}, location={self.location}, rating={self.rating}, date={self.date}, camera={self.camera_make} {self.camera_model})"


# ============================================================================
# Private implementation details below - users should not call these directly
# ============================================================================

def _read_xmp_from_jpg(photo_path):
    """Extract XMP metadata embedded in JPG file.

    Args:
        photo_path: Path to JPG file

    Returns:
        Dictionary with keys: keywords, location, rating (or None if no XMP found)
    """
    import xml.etree.ElementTree as ET

    try:
        with open(photo_path, 'rb') as f:
            content = f.read()

            # Find XMP packet in JPG
            xmp_start = content.find(b'<x:xmpmeta')
            xmp_end = content.find(b'</x:xmpmeta>')

            if xmp_start == -1 or xmp_end == -1:
                return None

            xmp_data = content[xmp_start:xmp_end + 12].decode('utf-8', errors='replace')

            # Parse XMP as XML
            root = ET.fromstring(xmp_data)

            # Define namespaces
            ns = {
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'xmp': 'http://ns.adobe.com/xap/1.0/',
                'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
            }

            xmp_metadata = {}

            # Extract keywords from dc:subject
            subject_bag = root.find('.//dc:subject/rdf:Bag', ns)
            if subject_bag is not None:
                keywords = []
                for li in subject_bag.findall('rdf:li', ns):
                    if li.text and not any(char.isdigit() or char == ',' for char in li.text):
                        # Filter out numeric values (like color coordinates)
                        keywords.append(li.text.strip())
                if keywords:
                    xmp_metadata['keywords'] = keywords

            # Extract location fields from photoshop and Iptc4xmpCore namespaces (can be attributes or elements)
            # Add Iptc4xmpCore namespace for sublocation
            ns['Iptc4xmpCore'] = 'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/'

            sublocation = None
            city = None
            state = None
            country = None

            # First try to find as attributes on rdf:Description
            for desc in root.findall('.//rdf:Description', ns):
                if not sublocation:
                    subloc_attr = desc.get('{http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/}Location')
                    if subloc_attr:
                        sublocation = subloc_attr

                if not city:
                    city_attr = desc.get('{http://ns.adobe.com/photoshop/1.0/}City')
                    if city_attr:
                        city = city_attr

                if not state:
                    state_attr = desc.get('{http://ns.adobe.com/photoshop/1.0/}State')
                    if state_attr:
                        state = state_attr

                if not country:
                    country_attr = desc.get('{http://ns.adobe.com/photoshop/1.0/}Country')
                    if country_attr:
                        country = country_attr

            # If not found as attributes, try as elements
            if not sublocation:
                subloc_elem = root.find('.//Iptc4xmpCore:Location', ns)
                if subloc_elem is not None and subloc_elem.text:
                    sublocation = subloc_elem.text

            if not city:
                city_elem = root.find('.//photoshop:City', ns)
                if city_elem is not None and city_elem.text:
                    city = city_elem.text

            if not state:
                state_elem = root.find('.//photoshop:State', ns)
                if state_elem is not None and state_elem.text:
                    state = state_elem.text

            if not country:
                country_elem = root.find('.//photoshop:Country', ns)
                if country_elem is not None and country_elem.text:
                    country = country_elem.text

            # Store location data if any field is present
            if sublocation or city or state or country:
                xmp_metadata['location'] = {
                    'sublocation': sublocation,
                    'city': city,
                    'state': state,
                    'country': country
                }

            # Extract rating from xmp:Rating (can be attribute or element)
            # First try to find it as an attribute on rdf:Description
            for desc in root.findall('.//rdf:Description', ns):
                rating_attr = desc.get('{http://ns.adobe.com/xap/1.0/}Rating')
                if rating_attr:
                    try:
                        xmp_metadata['rating'] = int(rating_attr)
                        break
                    except ValueError:
                        pass

            # If not found as attribute, try as element
            if 'rating' not in xmp_metadata:
                rating = root.find('.//xmp:Rating', ns)
                if rating is not None and rating.text:
                    try:
                        xmp_metadata['rating'] = int(rating.text)
                    except ValueError:
                        pass

            return xmp_metadata if xmp_metadata else None

    except Exception as e:
        return None


def _read_exif_data(photo_path):
    """Read EXIF data from photo (private helper).

    Args:
        photo_path: Path to JPG file

    Returns:
        Dictionary with EXIF data or empty dict
    """
    if not Image:
        return {}

    exif_data = {}

    try:
        img = Image.open(photo_path)
        exif = img.getexif()

        if not exif:
            return {}

        # Get EXIF IFD (where most camera settings are stored)
        exif_ifd = exif.get_ifd(0x8769)  # EXIF IFD tag

        # Helper function to process tags from either main EXIF or EXIF IFD
        def process_tags(tag_dict):
            for tag_id, value in tag_dict.items():
                tag_name = TAGS.get(tag_id, tag_id)

                # Date
                if tag_name in ('DateTime', 'DateTimeOriginal') and 'date' not in exif_data:
                    exif_data['date'] = value

                # Camera make and model
                elif tag_name == 'Make':
                    exif_data['camera_make'] = value.strip() if isinstance(value, str) else value
                elif tag_name == 'Model':
                    exif_data['camera_model'] = value.strip() if isinstance(value, str) else value

                # Lens
                elif tag_name == 'LensModel':
                    exif_data['lens_model'] = value.strip() if isinstance(value, str) else value

                # Focal length
                elif tag_name == 'FocalLength':
                    if isinstance(value, tuple):
                        exif_data['focal_length'] = round(value[0] / value[1], 1) if value[1] != 0 else float(value[0])
                    else:
                        # Handle IFDRational, int, float, or any numeric type
                        exif_data['focal_length'] = round(float(value), 1)

                # Aperture (FNumber)
                elif tag_name == 'FNumber':
                    if isinstance(value, tuple):
                        exif_data['aperture'] = round(value[0] / value[1], 1) if value[1] != 0 else float(value[0])
                    else:
                        # Handle IFDRational, int, float, or any numeric type
                        exif_data['aperture'] = round(float(value), 1)

                # Shutter speed (ExposureTime) - keep as string
                elif tag_name == 'ExposureTime':
                    if isinstance(value, tuple):
                        if value[0] == 1:
                            exif_data['shutter_speed'] = f"1/{value[1]}"
                        else:
                            exif_data['shutter_speed'] = f"{value[0] / value[1]:.2f}" if value[1] != 0 else str(value[0])
                    else:
                        # Handle IFDRational, int, float, or any numeric type
                        val = float(value)
                        if val < 1:
                            # Convert to fraction for fast shutter speeds
                            exif_data['shutter_speed'] = f"1/{int(1/val)}"
                        else:
                            exif_data['shutter_speed'] = f"{val:.2f}"

                # ISO
                elif tag_name in ('ISOSpeedRatings', 'ISO'):
                    exif_data['iso'] = int(value)

        # Process main EXIF tags
        process_tags(exif)

        # Process EXIF IFD tags (where camera settings usually are)
        if exif_ifd:
            process_tags(exif_ifd)

    except Exception as e:
        pass

    return exif_data


# ============================================================================
# Public API
# ============================================================================

def get_metadata(photo_path):
    """
    Get all metadata from a photo.

    This is the main entry point for reading photo metadata. It handles all
    the technical details of reading XMP, IPTC, and EXIF data automatically.

    Args:
        photo_path: Path or string path to JPG file

    Returns:
        PhotoMetadata object with:
            - keywords: List of keyword strings (lowercase)
            - location: City/location string or None
            - rating: Star rating (1-5) or None
            - date: Date string or None

        Returns None if the file doesn't exist.

    Example:
        metadata = get_metadata("my_photo.jpg")
        if metadata:
            print(f"Keywords: {metadata.keywords}")
            print(f"Rating: {metadata.rating}")
    """
    photo_path = Path(photo_path)

    if not photo_path.exists():
        return None

    metadata = PhotoMetadata(photo_path)

    # Read embedded metadata (XMP contains keywords, location, rating)
    xmp_data = _read_xmp_from_jpg(photo_path)
    if xmp_data:
        if 'keywords' in xmp_data:
            metadata.keywords = [kw.lower() for kw in xmp_data['keywords']]
        if 'location' in xmp_data:
            loc_data = xmp_data['location']
            metadata.location = Location(
                sublocation=loc_data.get('sublocation'),
                city=loc_data.get('city'),
                state=loc_data.get('state'),
                country=loc_data.get('country')
            )
        if 'rating' in xmp_data:
            metadata.rating = xmp_data['rating']

    # Read EXIF data (camera info, date, etc.)
    exif_data = _read_exif_data(photo_path)
    if exif_data:
        metadata.date = exif_data.get('date')
        metadata.camera_make = exif_data.get('camera_make')
        metadata.camera_model = exif_data.get('camera_model')
        metadata.lens_model = exif_data.get('lens_model')
        metadata.focal_length = exif_data.get('focal_length')
        metadata.aperture = exif_data.get('aperture')
        metadata.shutter_speed = exif_data.get('shutter_speed')
        metadata.iso = exif_data.get('iso')

    return metadata


def matches_filters(metadata, filters):
    """
    Check if photo metadata matches filter criteria.

    Args:
        metadata: PhotoMetadata object (from get_metadata)
        filters: Dictionary with optional filter criteria:
            - 'keywords': Comma-separated string (e.g., "street, urban")
            - 'location': City name (e.g., "Seattle")
            - 'rating': Rating filter (e.g., "4+", "5")
            - 'date': Date prefix (e.g., "2025", "2025-10")

    Returns:
        True if metadata matches ALL filter criteria, False otherwise

    Filter matching logic:
        - keywords: Photo must have at least ONE of the keywords (OR)
        - location: Exact match (case-insensitive)
        - rating: "4+" means rating >= 4, "5" means rating == 5
        - date: Prefix match ("2025" matches "2025-01-15", etc.)
        - All criteria combined with AND logic

    Example:
        filters = {'keywords': 'street, urban', 'rating': '4+'}
        if matches_filters(metadata, filters):
            print("Photo has (street OR urban) AND rating >= 4")
    """
    if not filters:
        return False

    # Check keywords (OR - must have at least one)
    if 'keywords' in filters:
        filter_keywords = [kw.strip().lower() for kw in filters['keywords'].split(',')]
        if filter_keywords:
            if not any(fk in metadata.keywords for fk in filter_keywords):
                return False

    # Check location (matches city, state, or country, case-insensitive)
    if 'location' in filters:
        if not metadata.location:
            return False

        filter_loc = filters['location'].lower()
        # Match if filter matches sublocation, city, state, or country
        matches = (
            (metadata.location.sublocation and filter_loc == metadata.location.sublocation.lower()) or
            (metadata.location.city and filter_loc == metadata.location.city.lower()) or
            (metadata.location.state and filter_loc == metadata.location.state.lower()) or
            (metadata.location.country and filter_loc == metadata.location.country.lower())
        )
        if not matches:
            return False

    # Check rating (e.g., "4+" means >= 4, "5" means exactly 5)
    if 'rating' in filters:
        rating_filter = filters['rating']
        if not metadata.rating:
            return False

        if '+' in rating_filter:
            min_rating = int(rating_filter.replace('+', ''))
            if metadata.rating < min_rating:
                return False
        else:
            exact_rating = int(rating_filter)
            if metadata.rating != exact_rating:
                return False

    # Check date (prefix match - "2025" matches "2025-01-15", etc.)
    if 'date' in filters:
        if not metadata.date or not str(metadata.date).startswith(filters['date']):
            return False

    return True
