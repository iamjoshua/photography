# photography
Some of my photos

## Preferred interface

The local web app in `interface/` is the preferred way to manage the
portfolio (browse the catalog visually, create and edit collections,
delete photos cleanly). Run it locally during the photo-management
workflow:

```
cd interface
npm install
npm run dev
```

The interface invokes the CLI scripts under `scripts/atomic/`
internally; every UI mutation is backed by an existing script. See
`interface/README.md` for details.

## Workflow: Lightroom to Website (CLI)

1. Export photos from Lightroom to `photos/imports/`
2. Run `./scripts/workflows/main`
3. Push to GitHub to trigger Vercel rebuild

That's it. The `main` workflow ingests exported photos directly into
the favorites collection (portfolio), generates metadata, builds
resized webp variants under `r2/`, and syncs `r2/` to Cloudflare R2.

To ingest into a different collection from the CLI:

```
./scripts/workflows/ingest-and-sync --collection <collection-name>
```

## Create a Filtered Collection

```
./scripts/atomic/create-collection seattle-pics --location "Seattle" --rating "4+"
./scripts/atomic/sync-collection seattle-pics
```

Filters: `--keywords`, `--location`, `--rating`, `--date`

Options: `--title`, `--description`

All of these can be edited in the generated YAML file at
`data/collections/<name>.yaml` afterwards.

## Repository layout

- `photos/` — local source jpgs (canonical: Lightroom; this repo is
  staging)
- `data/` — metadata yamls consumed by the website's static build
- `r2/` — local mirror of the Cloudflare R2 bucket (generated webp
  variants); gitignored
- `scripts/` — CLI scripts organized into `atomic/`, `workflows/`,
  and `legacy/`. See `scripts/README.md` for the methodology.
- `interface/` — local web app for data management. See
  `interface/README.md`.
