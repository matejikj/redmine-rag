# Task 11: Ollama Provider and Local LLM Runtime

## Goal

Enable local LLM inference through Ollama with model `mistral:7b-instruct-v0.3-q4_K_M`.

## Scope

- Add `ollama` as supported `LLM_PROVIDER`.
- Implement an Ollama client adapter for structured extraction and answer synthesis.
- Add runtime config for base URL, model, timeout, and concurrency.
- Expose provider/model readiness in health checks.

## Deliverables

- Config keys: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_S`, `OLLAMA_MAX_CONCURRENCY`.
- `OllamaStructuredExtractionClient` integrated into provider factory.
- Shared LLM runtime abstraction usable by extraction and ask services.
- Runbook section for installing/pulling model and validating local runtime.

## Acceptance Criteria

- With `LLM_PROVIDER=ollama`, extraction can call local Ollama successfully.
- Default model can be set to `mistral:7b-instruct-v0.3-q4_K_M` via config only.
- System fails fast with actionable error when model is unavailable.
- `/healthz` reports degraded status when Ollama is unreachable.

## Quality Gates

- Integration tests with mocked Ollama HTTP responses.
- Failure tests for timeout and connection refusal.
- Documentation updated in local-dev and operations runbooks.
