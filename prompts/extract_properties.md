Extract structured issue properties from the provided issue and journals.
Return valid JSON that matches the schema:
{
  "topic": "string|null",
  "module": "string|null",
  "problem_type": "string|null",
  "root_cause": "string|null",
  "resolution_type": "string|null",
  "customer_impact": "low|medium|high|null",
  "risk_flags": ["string"],
  "next_actions": ["string"],
  "confidence": 0.0
}

Rules:
- Use null when unknown.
- Do not invent facts.
- Keep values normalized and short.
