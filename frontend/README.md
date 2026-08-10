# CodioLive frontend

The React/Vite client for Mock Interview Hub uses the generated OpenAPI
client in `src/lib/api-client` and the shared adapter in `src/lib/api.ts`.

## Development

```sh
npm ci
npm run dev
npm run typecheck
npm run lint
```

The Radix/shadcn components under `src/components/ui` are a shared component
inventory; unused primitives are intentionally retained for future screens,
but they must not be imported to bypass the generated API or security
boundaries. Collaborative execution is disabled until an isolated runtime is
approved. Monaco assets/workers are bundled same-origin in the production
image; no third-party CDN is required at runtime.

Production uses the repository Render Docker image and `/api` same-origin
proxy. Do not add browser secrets, standalone guest-auth calls, or raw fetches
that bypass the generated client contracts.
