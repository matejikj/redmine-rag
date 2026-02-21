# Frontend Console

Vite + React + TypeScript frontend for Redmine RAG operator workflows.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Dev server runs at `http://127.0.0.1:5173` and proxies `/v1/*` and `/healthz` to backend at `http://127.0.0.1:8000`.

## Build for backend serving

```bash
cd frontend
npm run build
```

Backend serves build output under `http://127.0.0.1:8000/app`.

## Tests

```bash
npm run test
npm run test:e2e
```
