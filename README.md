# photography
Some of my photos

## Workflow: Lightroom to Website

1. Export photos from Lightroom to `photos/exports/`
2. Run `./scripts/main`
3. Push to GitHub to trigger Vercel rebuild

That's it. The `main` script is the single entry point for the current workflow. Right now it imports exported photos directly into the favorites collection (portfolio), generates metadata, and uploads to R2. As new collections and workflows are added, `main` will be updated to route to the right process.

## Create a Filtered Collection

```
./scripts/create-collection seattle-pics --location "Seattle" --rating "4+"
./scripts/sync-collection seattle-pics
```

Filters: `--keywords`, `--location`, `--rating`, `--date`

Options: `--title`, `--description`

All of these can be edited in the generated YAML file at `data/collections/<name>.yaml` afterwards.
