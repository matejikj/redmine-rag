# Task 14: LLM Safety Guardrails and Output Validation

## Goal

Protect user-facing answers from unsafe behavior, policy violations, and ungrounded output.

## Scope

- Add guardrail layer for prompt injection and context exfiltration attempts.
- Define denylist and policy checks for unsupported actions.
- Validate answer structure, citation references, and content safety before response.
- Classify and log rejection reasons with deterministic buckets.

## Deliverables

- Guardrail service integrated into ask and extraction LLM paths.
- Rejection categories (`prompt_injection`, `ungrounded_claim`, `schema_violation`, `unsafe_content`).
- Safe fallback response templates for rejected generations.
- Security runbook updates with example incidents and response actions.

## Acceptance Criteria

- Known adversarial prompts are blocked and logged with explicit reason.
- Unsafe or malformed model outputs are never returned directly to user.
- Guardrail checks are deterministic and testable.
- Health/ops visibility includes guardrail rejection counters.

## Quality Gates

- Red-team style test suite for injection and jailbreak attempts.
- Contract tests for citation and schema validation failures.
- Metrics dashboard can track rejection rate by reason.
