# photography
Some of my photos

## Workflow: Lightroom to Website

1. Export photos from Lightroom to `photos/exports/`
2. Run `./scripts/run-all` (from terminal or double click in finder)
3. Push to GitHub to trigger Vercel rebuild

That's it. The script ingests photos, generates metadata, syncs collections, and publishes to R2.

## Add a Photo to Favorites

```
./scripts/add-to-favorites <drag photo here>
```

Drop the image onto the terminal to paste its path.

## Create a Filtered Collection

```
./scripts/create-collection seattle-pics --location "Seattle" --rating "4+"
./scripts/sync-collection seattle-pics
```

Filters: `--keywords`, `--location`, `--rating`, `--date`

Options: `--title`, `--description`

All of these can be edited in the generated YAML file at `data/collections/<name>.yaml` afterwards.
