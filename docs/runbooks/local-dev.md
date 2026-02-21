# Local Development Runbook

## Setup

```bash
cp .env.example .env
make bootstrap
make migrate
```

## Start API

```bash
make dev
```

## Basic smoke test

```bash
curl http://127.0.0.1:8000/healthz
```

## Trigger sync

```bash
curl -X POST http://127.0.0.1:8000/v1/sync/redmine -H 'content-type: application/json' -d '{}'
```
