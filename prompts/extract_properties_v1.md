You are extracting structured issue properties from Redmine issue evidence.

Output strictly valid JSON only.
Do not include markdown fences or explanatory text.

Schema contract:
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
- Use only facts from input issue and journals.
- If information is missing, use null or empty list.
- Keep values normalized and short.
- Confidence must be in range 0.0 to 1.0.
