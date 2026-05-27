# interface

A local-only web app for managing the photography portfolio data
(collections, photo metadata, deletions). Lives in this repo
alongside the data and scripts it operates on. Run locally during
the photo-management workflow. Never deployed publicly.

## Why this exists

The CLI scripts in `scripts/` handle the full ingest/build/sync
workflow, but a few operations have become a choke point:

- Spotting duplicates and stale files left behind after renames or
  location changes in Lightroom. The catalog has to be inspected
  manually across `photos/` and `data/photos/` to find them.
- Removing a single photo from the portfolio entirely. Today this
  requires manual deletes across `photos/`, `data/photos/`, `r2/`,
  and every collection yaml that references it — easy to miss one
  and leave orphans.
- Creating and editing collections. The flow exists via CLI but is
  awkward enough that it discourages adding new ones.

The goal is to make these workflows a few clicks instead of a
manual multi-step procedure across four directories.

## Architectural constraint

**The CLI is the source of truth. The UI is a disposable layer.**

- Every mutation the UI performs must invoke an existing script in
  `scripts/`. The UI's server code does not contain write logic
  that duplicates a script. If a needed mutation doesn't have a
  script, the script gets built first.
- Reads are fine to do directly — rendering the catalog by reading
  `data/`, `photos/`, and `r2/` is not a mutation.
- If this interface is abandoned, deleted, or breaks, the rest of
  the repo continues working exactly as it does today via the CLI.
  That property must hold at all times.

## Running

```bash
cd interface
npm install
npm run dev
```

Open http://localhost:4321.

## Stack

- Astro 5 (SSR, Node adapter) — same framework family as the `me` repo.
- TypeScript, zero UI framework. Interactive bits (lightbox, photo
  menu, theme toggle) are vanilla TS modules under `src/components/`.
- `yaml` for parsing collection/photo metadata.

## File layout

```
src/
├── pages/
│   ├── index.astro                          all photos
│   ├── imports.astro                        pending imports waiting to be ingested
│   ├── collections/new.astro                create form
│   ├── collections/[name].astro             edit a collection
│   └── api/
│       ├── img/[...path].ts                 serves r2/{small,large} + photos/imports
│       ├── photos/delete.ts                 cascading delete
│       ├── imports/import.ts                bulk-ingest photos/imports
│       └── collections/
│           ├── index.ts                     GET list (for menus)
│           ├── create.ts
│           └── [name]/{update,add-photo,remove-photo}.ts
├── components/
│   ├── Layout.astro · Sidebar.astro
│   ├── PhotoGrid.astro · PhotoCard.astro    portfolio photos
│   ├── ImportGrid.astro · ImportCard.astro  pending-import tiles (inert, no menu)
│   ├── ImportToolbar.astro                  bulk destination picker for /imports
│   ├── Lightbox.ts                          large-image proofing overlay (photos only)
│   ├── PhotoMenu.ts                         3-dot + right-click + submenu (photos only)
│   └── ThemeToggle.ts                       light/dark persistence
├── lib/
│   ├── paths.ts                             resolves repo root and key dirs
│   ├── catalog.ts                           reads data/photos + r2/ → Photo[]
│   ├── collections.ts                       reads data/collections/*.yaml
│   ├── imports.ts                           reads photos/imports/ → PendingImport[]
│   └── runScript.ts                         the only place that mutates state
├── styles/
│   ├── tokens.css                           light + dark design tokens
│   └── global.css
└── types.ts
```

One purpose per file. Every API endpoint is a thin wrapper around
`runScript()`.

## Script contract

The interface invokes the following scripts. All atomic scripts live
under `scripts/atomic/`; the ingest workflow lives under
`scripts/workflows/`. See `scripts/README.md` for the methodology
behind the two layers.

| Script | Path | Args | Used by |
| --- | --- | --- | --- |
| `create-collection` | `scripts/atomic/` | `<name> --title T [--description D] [--keywords K] [--location L] [--rating R] [--date D]` | `POST /api/collections/create` |
| `sync-collection` | `scripts/atomic/` | `<name>` | `POST /api/collections/create` (when filters supplied) |
| `add-to-collection` | `scripts/atomic/` | `<name> <photo-path>` | `POST /api/collections/[name]/add-photo` |
| `remove-from-collection` | `scripts/atomic/` | `<name> <photo-path>` | `POST /api/collections/[name]/remove-photo` |
| `update-collection` | `scripts/atomic/` | `<name> [--title T] [--description D]` | `POST /api/collections/[name]/update` |
| `delete-photo` | `scripts/atomic/` | `<photo-path>` | `POST /api/photos/delete` |
| `ingest-and-sync` | `scripts/workflows/` | `[--collection NAME]` | `POST /api/imports/import` |

Cascade semantics for the destructive ones:

- `delete-photo <path>` — remove the source jpg in `photos/`, the
  metadata yaml in `data/photos/`, the small + large variants in
  `r2/`, and every reference to `<path>` in every
  `data/collections/*.yaml`. Idempotent (skipping already-missing
  pieces, not failing).
- `remove-from-collection <name> <path>` — remove just the photo
  entry from the named collection's yaml. The photo itself stays
  in the portfolio.
- `update-collection <name>` — patch the named collection yaml's
  `title` and/or `description` without touching its `photos:` list.

Behavior for the import flow:

- `ingest-and-sync [--collection NAME]` — full pipeline workflow:
  1. Move every file currently in `photos/imports/` to its proper
     home under `photos/<year>/<region>/<filename>.jpg` (per EXIF
     date and location).
  2. If `--collection NAME` was passed, add every ingested photo
     to that collection's yaml. Without the flag, the photos enter
     the catalog but no collection.
  3. Generate the metadata yamls in `data/photos/`.
  4. Build small + large webp variants under `r2/`.
  5. Sync local `r2/` to the Cloudflare R2 bucket.

  Idempotent on empty input (no-op if `photos/imports/` is empty).
  Only one `--collection` flag is supported by the UI; if the user
  wants a photo in multiple collections, they ingest first, then
  use the existing "Add to collection" action.

## Image serving

The dev server exposes:

- `/api/img/small/<path>.webp` — from `r2/small/`
- `/api/img/large/<path>.webp` — from `r2/large/`
- `/api/img/import/<path>` — raw original from `photos/imports/`

All stream directly from disk. No copying or symlinking.
