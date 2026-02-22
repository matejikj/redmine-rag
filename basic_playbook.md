# Basic End-to-End Playbook (Mock Redmine + Local LLM + GUI)

This guide is the fastest way to run the full app end-to-end with:
- Mock Redmine data source
- Local Ollama model (`mistral:7b-instruct-v0.3-q4_K_M`)
- GUI workflows (`Sync -> Metrics -> Ask -> Ops`)

## 1. Prerequisites

- Python `3.12+`
- `make`
- `git`
- `ollama` installed and running locally
- Node.js/npm (for frontend)

## 2. One-time setup

```bash
cp .env.example .env
```

Set `.env` for mock + local LLM:

```env
REDMINE_BASE_URL=http://127.0.0.1:8081
REDMINE_API_KEY=mock-api-key
REDMINE_ALLOWED_HOSTS=127.0.0.1,localhost
REDMINE_PROJECT_IDS=1

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=mistral:7b-instruct-v0.3-q4_K_M
ASK_ANSWER_MODE=llm_grounded
LLM_EXTRACT_ENABLED=true
```

Install backend + frontend dependencies and DB schema:

```bash
make bootstrap
make migrate
make ui-install
```

## 3. Prepare local model

```bash
ollama pull mistral:7b-instruct-v0.3-q4_K_M
ollama list
```

## 4. Start services

Terminal A (Mock Redmine):

```bash
MOCK_REDMINE_DATASET_PROFILE=small make mock-redmine
```

Terminal B (API):

```bash
make dev
```

Terminal C (Frontend GUI):

```bash
make ui-dev
```

Open:
- API docs: `http://127.0.0.1:8000/docs`
- GUI: `http://127.0.0.1:5173`

## 5. Run end-to-end flow in GUI

### 5.1 Sync page

1. Open `Sync`.
2. Set `Project scope` to `1`.
3. Click `Start sync`.
4. Wait for job status `finished` and inspect summary.

### 5.2 Metrics page

1. Open `Metrics`.
2. Keep `Project IDs=1`, set date window if needed.
3. Click `Apply filters`.
4. Click `Run extraction`.
5. Confirm extraction counters are visible.

### 5.3 Ask page

1. Open `Ask`.
2. Ask question (example):
   - `What is the login callback issue and rollback plan?`
3. Verify:
   - answer generated
   - citations visible and clickable
   - claim-to-citation mapping works

### 5.4 Ops page

1. Open `Ops`.
2. Verify runtime cards (`LLM provider/model`, health snapshot).
3. Click `Run backup`.
4. Click `Run maintenance`.
5. Confirm both actions appear in `Operations Run History`.

## 6. Optional API spot checks

```bash
curl http://127.0.0.1:8000/healthz
curl "http://127.0.0.1:8000/v1/sync/jobs?limit=20"
curl "http://127.0.0.1:8000/v1/metrics/summary?project_ids=1"
curl http://127.0.0.1:8000/v1/evals/latest
curl http://127.0.0.1:8000/v1/ops/environment
curl "http://127.0.0.1:8000/v1/ops/runs?limit=20"
```

## 7. Verify project quality gates

```bash
make format
make check
cd frontend && npm run test:e2e
```

Optional regression gate:

```bash
make eval-gate
```

## 8. Troubleshooting

- If `/healthz` shows LLM runtime warning:
  - verify Ollama is running on `127.0.0.1:11434`
  - verify model exists: `ollama list`
- If first sync fails:
  - check Mock Redmine is running on `127.0.0.1:8081`
  - retry from `Sync` page

## 9. Stop services

- Stop `make ui-dev` with `Ctrl+C`
- Stop `make dev` with `Ctrl+C`
- Stop `make mock-redmine` with `Ctrl+C`
