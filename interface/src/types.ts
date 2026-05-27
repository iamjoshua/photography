export interface PhotoLocation {
  sublocation: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
}

export interface Photo {
  /** Path without extension, e.g. "2025/washington/foo" — used as a stable ID */
  id: string;
  /** Original `.jpg` path as stored in the photo's yaml */
  path: string;
  filename: string;
  keywords: string[];
  location: PhotoLocation;
  rating: number | null;
  date: string | null;
  camera_make: string | null;
  camera_model: string | null;
  lens_model: string | null;
  focal_length: number | null;
  aperture: number | null;
  shutter_speed: string | null;
  iso: number | null;
  hasSmall: boolean;
  hasLarge: boolean;
  collections: string[];
}

export interface CollectionPhotoRef {
  path: string;
  caption: string;
  alt: string;
}

export interface Collection {
  /** Filename without `.yaml` */
  name: string;
  title: string;
  description: string;
  cover_path: string;
  filters?: Record<string, string>;
  photos: CollectionPhotoRef[];
}
