# scripts

All script entry points live in one of three subdirectories. Nothing
sits at the root of `scripts/` except this README.

## atomic/

One responsibility per script. Atomics do not call each other.
Python helpers for the atomic scripts live in `atomic/utils/`.

Current atomics:

- `ingest-photos` — move files from `photos/imports/` into
  `photos/<year>/<location>/`. Supports `--output-paths <file>` to
  emit the moved destination paths (used by workflows).
- `generate-photo-metadata-files` — generate / refresh
  `data/photos/**/*.yaml` from photo EXIF + IPTC metadata.
- `create-collection <name> [filters]` — create a collection yaml
  (filtered or manual).
- `add-to-collection <name> <photo-path>` — add a photo to a
  collection.
- `remove-from-collection <name> <photo-path>` — remove a photo from
  a single collection. Idempotent.
- `update-collection <name> [--title T] [--description D] [--cover-path PATH]` —
  patch a collection's title, description, and/or cover_path without
  touching its photos list.
- `delete-photo <photo-path>` — cascade-remove a photo across
  `photos/`, `data/photos/`, `r2/{small,large}/`, and every collection
  yaml. Idempotent.
- `sync-collection <name | --all>` — refresh a filtered collection's
  photo list from current metadata.
- `build-r2` — build the local `r2/small/` and `r2/large/` webp
  variants from sources in `photos/`.
- `sync-to-r2` — mirror local `r2/` to the Cloudflare R2 bucket
  (uploads adds, deletes removals).

## workflows/

Compositions of atomic scripts. A workflow is named for the full
outcome it produces, and its body is a sequence of calls into
`atomic/`. Workflows never duplicate logic from atomic scripts; if a
workflow needs to do something new, the new behavior goes into a new
atomic first.

Current workflows:

- `main` — the canonical user entry point. Calls
  `ingest-and-sync --collection favorites`.
- `ingest-and-sync [--collection NAME]` — full pipeline: ingest from
  `photos/imports/`, optionally add the ingested photos to a named
  collection, generate metadata, build `r2/` variants, sync to R2.

## legacy/

Scripts that are no longer part of the active workflow but kept here
in case they turn out to still be needed. New code must not depend on
anything in `legacy/`. If something here proves necessary, lift it
into `atomic/` or `workflows/` deliberately.

## Naming and vocabulary

Workflow names and the atomic names they compose are intended to read
coherently together. For example, `ingest-and-sync` chains
`ingest-photos` → `generate-photo-metadata-files` → `build-r2` →
`sync-to-r2`. The verb `sync` is preferred over `publish` because the
operation is bidirectional state mirroring (adds *and* removes), not
one-way publishing.

## Setup

Python 3 plus a few libraries:

```bash
pip3 install pyyaml iptcinfo3 Pillow boto3
```

Cloudflare R2 credentials live in `.r2config` at the repo root (copy
from `.r2config.example`).
