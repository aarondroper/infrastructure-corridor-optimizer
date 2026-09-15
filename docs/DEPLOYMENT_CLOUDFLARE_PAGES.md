# Cloudflare Pages deployment

## Status

The static application is live and verified at
`https://infrastructure-corridor-optimizer.aaronroper.workers.dev/`. The hostname
supplied for verification omitted the initial `i` and does not resolve. The live
hostname is a `workers.dev` origin rather than the documented `pages.dev` origin, so
the public response does not establish a Cloudflare Pages project name or expose the
account's source commit metadata. The deployed shell, route asset, and hashed bundles
do match the local production artifact for commit `6c4d543` byte-for-byte.

The application is therefore verified as a live Cloudflare static deployment. The
owner should confirm in the Cloudflare dashboard whether this `workers.dev` hostname
is an intentional alias or a separate Worker delivery. No Pages-specific project
identity is claimed from HTTP evidence alone.

## Application shape

The application is a static Vite build. It has no server-side code, Functions,
Workers, database, secrets, or build-time environment variables. The Python
preprocessing pipeline is run before publication; the browser consumes the compact
`data/routes.json` asset and requests OpenStreetMap raster tiles at runtime.

The frontend is a subproject, so configure Pages with:

| Setting | Value |
| --- | --- |
| Repository | this GitHub repository, connected through Pages Git integration |
| Root/project directory | `web` |
| Build command | `npm run build` |
| Build output directory | `dist` (relative to `web`) |
| Production branch | `main` |
| Environment variables | none |

Cloudflare Pages supports a custom root directory for monorepos and the Vite default
build/output pair is `npm run build` and `dist`. See the [Pages build configuration
documentation](https://developers.cloudflare.com/pages/configuration/build-configuration/)
and [Vite deployment guide](https://developers.cloudflare.com/pages/framework-guides/deploy-a-vite3-project/).

## Repository configuration

`web/vite.config.ts` explicitly emits `dist` and does not emit source maps. The
compact analytical asset is copied from `web/public/data/routes.json` into the build.
`web/public/_headers` instructs Cloudflare Pages to cache Vite's content-hashed
`/assets/*` files for one year as immutable. The stable `/data/routes.json` asset is
not marked immutable, so a future deployment can replace it without a stale-name
assumption. No `_redirects` file is required: the MVP has only the root application
URL and no client-side route paths.

## Local release verification

From the repository root:

```bash
cd web
npm run build
ICO_PREVIEW_PORT=4174 PLAYWRIGHT_BROWSERS_PATH=/tmp/ico-browser-cache npm run test:browser
```

The browser suite uses `vite preview` against the built `dist` directory. It verifies
the root load and reload, static shell and data-asset responses, route switching,
impact inspection, GeoJSON/CSV downloads, keyboard focus, responsive viewports, the
asset error state, and successful OpenStreetMap tile responses when the public tile
service is reachable. `ICO_PREVIEW_PORT` avoids collisions with another local
preview server.

The verified local build for the current interface-polish tree currently contains:

- `index.html` — 474 bytes;
- hashed CSS — 93,599 bytes;
- hashed JavaScript — 1,182,110 bytes;
- `data/routes.json` — 327,336 bytes;
- `_headers` — 63 bytes.

The build shell and compact analytical asset contain no local filesystem paths,
development hostnames, or raw/cache source references. `web/dist/` remains ignored by
Git, as do source GIS data and caches.

## Live production verification

On 15 September 2026, bounded HTTPS checks returned `200` for the root shell,
`/data/routes.json`, hashed JavaScript, and hashed CSS. The public route JSON was
327,336 bytes with three routes and two endpoints, and its SHA-256 matched the local
asset:

`35eeb0995773d6ebc4ca65653666da226d902cb0926f8a8ca305a95a0e8f6127`

The public JavaScript and CSS SHA-256 values also matched the local build. Cloudflare
served `public, max-age=31536000, immutable` for both hashed assets and
`public, max-age=0, must-revalidate` for the stable route JSON, as intended.

The public-origin Playwright suite passed all three tests at 1440×900, 1280×800,
768×1024, and 390×844. It verified root reload, route switching, endpoint/route
visibility, impact inspection, statistics, GeoJSON and CSV exports, focus behavior,
responsive layout, asset failure handling, and successful OpenStreetMap responses.
Strict network capture found no console/page errors or genuine failed requests. It did
observe expected `net::ERR_ABORTED` cancellations for obsolete OSM tiles while MapLibre
settled the camera; successful tile responses were also observed.

The current interface-polish tree has separately passed the same production-preview
browser suite and visual screenshot review at all four viewports. That local evidence
does not change the public deployment claim until this commit is released through the
Cloudflare workflow.

## Owner deployment steps

1. In Cloudflare, open **Workers & Pages → Create application → Pages → Connect to
   Git** and authorize the GitHub repository.
2. Select the repository and production branch `main`.
3. Set **Root directory** to `web`.
4. Set **Build command** to `npm run build` and **Build output directory** to `dist`.
5. Leave environment variables empty and deploy.
6. Return the resulting `*.pages.dev` URL and deployed commit, if shown, for final
   Pages-specific verification. The currently verified public origin is the
   `workers.dev` URL recorded above.

The Git integration method is preferred because it provides commit-linked builds and
preview deployments. A direct upload is not needed for this repository. Pages can
publish the static output without any additional Cloudflare service.

## Remaining account-level check

The public application has passed live verification, but the Cloudflare account
dashboard should confirm the project name, delivery product, source repository, and
deployed commit. If this is a Worker rather than a Pages project, either document that
intentional deviation or create the Pages Git-integrated deployment described above;
do not infer the project identity from the `workers.dev` hostname alone.
