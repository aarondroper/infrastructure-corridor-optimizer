# Cloudflare Pages deployment

## Status

The repository is prepared for Cloudflare Pages, but no public deployment has been
created or verified. Cloudflare account authorization and GitHub repository access are
the only remaining deployment steps for this milestone.

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

The verified build currently contains:

- `index.html` — 474 bytes;
- hashed CSS — 88,943 bytes;
- hashed JavaScript — 1,181,091 bytes;
- `data/routes.json` — 327,336 bytes;
- `_headers` — 63 bytes.

The build shell and compact analytical asset contain no local filesystem paths,
development hostnames, or raw/cache source references. `web/dist/` remains ignored by
Git, as do source GIS data and caches.

## Owner deployment steps

1. In Cloudflare, open **Workers & Pages → Create application → Pages → Connect to
   Git** and authorize the GitHub repository.
2. Select the repository and production branch `main`.
3. Set **Root directory** to `web`.
4. Set **Build command** to `npm run build` and **Build output directory** to `dist`.
5. Leave environment variables empty and deploy.
6. Return the resulting `*.pages.dev` URL and deployed commit, if shown, for final
   browser/network/export verification.

The Git integration method is preferred because it provides commit-linked builds and
preview deployments. A direct upload is not needed for this repository. Pages can
publish the static output without any additional Cloudflare service.

## Post-deployment verification

The public URL must still be verified before `PROJECT_STATE.md` can claim deployment
completion. Check the root load and reload at desktop and narrow/mobile widths, route
switching, exports, the `/data/routes.json` response, hashed asset responses, browser
console/runtime errors, failed requests, and OpenStreetMap tile behavior. Confirm that
the deployed commit matches the intended repository commit.
