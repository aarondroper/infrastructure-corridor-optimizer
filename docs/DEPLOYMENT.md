# Deployment

The application is a static React/TypeScript + MapLibre build. It has no
functions, Workers code, database, server-side API, or runtime environment
variables.

## Verified live state

The public application is live at:

`https://infrastructure-corridor-optimizer.aaronroper.workers.dev`

The static origin has been verified with the production browser checks recorded
in the repository history. The hostname alone does not establish a Cloudflare
account or project identity, so release documentation records the public result
without claiming an unverified Pages project association.

## Build contract

| Setting | Value |
| --- | --- |
| production branch | `main` |
| project/root directory | `web` |
| build command | `npm run build` |
| output directory | `dist` relative to `web` (`web/dist`) |
| environment variables | none expected |
| runtime services | none |

Run the release build from the frontend root:

```bash
cd web
npm ci
npm run build
```

The build emits the Vite application into `web/dist`. `_headers` is copied into
the output and applies long-lived caching to hashed JavaScript, CSS, font, and
image assets, while keeping `data/routes.json` short-lived enough to make an
updated published analytical asset observable. There is no `_redirects` file:
the current application uses a single entry document and does not require
client-side page routing.

## Release verification

Before publishing a build, verify:

```bash
cd web
npm run build
npm run test:browser
```

Serve `web/dist` with a production-style static server and check the application
at 1440×900, 1280×800, 768×1024, and 390×844. Confirm all three precomputed
routes, `/data/routes.json`, the map tiles and attribution, GeoJSON/CSV downloads,
and the absence of failed asset requests or console errors. Do not include raw
GIS data, caches, or intermediate analytical artifacts in the published output.

## Deployment methods

The repository is compatible with a Git-integrated Cloudflare Pages project using
the build contract above and `main` as its production branch. A direct static
upload of the same `web/dist` output is equivalent for this architecture. Use
the repository-integrated method when account access is available so releases
remain tied to commits; the public URL must still be verified after each live
release before project state is updated.
