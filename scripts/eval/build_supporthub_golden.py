from __future__ import annotations

import json
from pathlib import Path

OUTPUT_PATH = Path("evals/supporthub_golden_v1.jsonl")


def issue(source_id: int) -> dict[str, object]:
    return {"source_type": "issue", "source_id": source_id}


def journal(issue_id: int, journal_id: int) -> dict[str, object]:
    return {
        "source_type": "journal",
        "source_id": f"{issue_id}#{journal_id}",
        "issue_id": issue_id,
        "journal_id": journal_id,
    }


def attachment(issue_id: int, attachment_id: int) -> dict[str, object]:
    return {
        "source_type": "attachment",
        "source_id": f"{issue_id}#{attachment_id}",
        "issue_id": issue_id,
        "attachment_id": attachment_id,
    }


def wiki(title: str) -> dict[str, object]:
    return {"source_type": "wiki", "source_id": title}


def news(source_id: int) -> dict[str, object]:
    return {"source_type": "news", "source_id": source_id}


def document(source_id: int) -> dict[str, object]:
    return {"source_type": "document", "source_id": source_id}


def file_ref(source_id: int) -> dict[str, object]:
    return {"source_type": "file", "source_id": source_id}


def message(source_id: int) -> dict[str, object]:
    return {"source_type": "message", "source_id": source_id}


def make_query(
    query_id: str,
    text: str,
    answer_type: str,
    sources: list[dict[str, object]],
    *,
    difficulty: str,
    tags: list[str],
    language: str = "cs",
    include_private: bool = False,
) -> dict[str, object]:
    source_types = sorted({str(item["source_type"]) for item in sources})
    return {
        "id": query_id,
        "query": text,
        "language": language,
        "difficulty": difficulty,
        "expected_answer_type": answer_type,
        "filters": {"project_id": "1", "include_private": include_private},
        "expected_source_types": source_types,
        "expected_sources": sources,
        "tags": tags,
    }


def build_queries() -> list[dict[str, object]]:
    queries: list[dict[str, object]] = []

    # Core project features and incidents (1-10)
    queries.extend(
        [
            make_query(
                "gq-001",
                "Jaké vlastnosti má login feature v SupportHubu a jaké jsou hlavní rizika?",
                "feature_overview",
                [issue(101), journal(101, 1001), wiki("Feature-Login"), document(92001)],
                difficulty="basic",
                tags=["auth", "feature", "overview"],
            ),
            make_query(
                "gq-002",
                "What is the root cause path for Safari callback timeout "
                "and what evidence supports it?",
                "root_cause_summary",
                [issue(102), journal(102, 1003), message(95003), file_ref(93001)],
                difficulty="basic",
                tags=["auth", "bug", "root-cause"],
                language="en",
            ),
            make_query(
                "gq-003",
                "Shrň incident triage playbook a jak navazuje na reálné incidenty.",
                "action_plan",
                [wiki("Incident-Triage-Playbook"), issue(103), issue(301), news(91101)],
                difficulty="basic",
                tags=["operations", "playbook", "incident"],
            ),
            make_query(
                "gq-004",
                "How is the evidence timeline architecture grounded in project artifacts?",
                "architecture_summary",
                [issue(201), wiki("Reporting-Citations"), news(91002), document(92002)],
                difficulty="basic",
                tags=["timeline", "citations", "architecture"],
                language="en",
            ),
            make_query(
                "gq-005",
                "Co je známé z privátní security review k token replay mitigaci?",
                "risk_assessment",
                [issue(301), journal(301, 3001), message(95999), document(92101)],
                difficulty="advanced",
                tags=["security", "private", "risk"],
                include_private=True,
            ),
            make_query(
                "gq-006",
                "Kde jsou zaznamenané rollout readiness rozhodnutí pro OAuth?",
                "decision_log",
                [message(95001), message(95002), issue(101), document(92001)],
                difficulty="basic",
                tags=["decision", "rollout", "auth"],
            ),
            make_query(
                "gq-007",
                "Compare issue #101 and #102 and explain dependency direction.",
                "comparison",
                [issue(101), issue(102), journal(101, 1001), message(95003)],
                difficulty="basic",
                tags=["dependency", "comparison", "auth"],
                language="en",
            ),
            make_query(
                "gq-008",
                "Jaké zdroje podporují tvrzení o citation strategii a traceability?",
                "evidence_check",
                [wiki("Reporting-Citations"), issue(201), news(91002), document(92101)],
                difficulty="basic",
                tags=["citations", "traceability", "evidence"],
            ),
            make_query(
                "gq-009",
                "What operational follow-up was agreed for callback stability after rollout?",
                "action_plan",
                [issue(102), message(95001), message(95002), news(91001)],
                difficulty="advanced",
                tags=["operations", "follow-up", "callback"],
                language="en",
            ),
            make_query(
                "gq-010",
                "Vysvětli vztah mezi incident runbookem a security board trail.",
                "communication_summary",
                [wiki("Incident-Triage-Playbook"), message(95999), issue(301), document(92101)],
                difficulty="advanced",
                tags=["security", "runbook", "communication"],
                include_private=True,
            ),
        ]
    )

    reopened_ids = [1039, 1052, 1104, 1117, 1169, 1182]
    stalled_ids = [1111, 1148]
    misprioritized_ids = [1029, 1058, 1174, 1203]
    attachment_ids = [1000, 1004, 1020, 1040, 1052, 1060]

    # Backlog and edge-case scenarios (11-28)
    for idx, issue_id in enumerate(reopened_ids, start=11):
        queries.append(
            make_query(
                f"gq-{idx:03d}",
                f"Why was issue #{issue_id} reopened and what evidence supports "
                "the false closure path?",
                "incident_timeline",
                [
                    issue(issue_id),
                    wiki(f"Root-Cause-Catalog-{(idx % 20) + 1}"),
                    document(92100 + ((idx + 2) % 18)),
                    message(96000 + ((idx % 12) * 2)),
                ],
                difficulty="advanced",
                tags=["reopened", "timeline", "edge-case"],
                language="en",
            )
        )

    for idx, issue_id in enumerate(stalled_ids, start=17):
        queries.append(
            make_query(
                f"gq-{idx:03d}",
                f"Co blokuje issue #{issue_id} a jaké jsou doporučené další kroky?",
                "action_plan",
                [
                    issue(issue_id),
                    wiki(f"Escalation-Policy-{(idx % 20) + 1}"),
                    document(92100 + ((idx + 5) % 18)),
                    message(96000 + ((idx % 12) * 2)),
                ],
                difficulty="advanced",
                tags=["stalled", "escalation", "plan"],
            )
        )

    for idx, issue_id in enumerate(misprioritized_ids, start=19):
        queries.append(
            make_query(
                f"gq-{idx:03d}",
                f"Assess priority inconsistency for issue #{issue_id} "
                "and recommend priority correction.",
                "risk_assessment",
                [
                    issue(issue_id),
                    wiki(f"SLA-Metrics-Guide-{(idx % 20) + 1}"),
                    news(91100 + (idx % 15)),
                    document(92100 + ((idx + 7) % 18)),
                ],
                difficulty="advanced",
                tags=["priority", "sla", "edge-case"],
                language="en",
            )
        )

    for idx, issue_id in enumerate(attachment_ids, start=23):
        attachment_id = 60000 + (issue_id - 1000)
        queries.append(
            make_query(
                f"gq-{idx:03d}",
                f"Jaké technické důkazy z attachmentů jsou klíčové pro issue #{issue_id}?",
                "evidence_check",
                [
                    issue(issue_id),
                    attachment(issue_id, attachment_id),
                    file_ref(93100 + (idx % 24)),
                    wiki(f"Evidence-Timeline-FAQ-{(idx % 20) + 1}"),
                ],
                difficulty="basic",
                tags=["attachments", "evidence", "citations"],
            )
        )

    # SLA, time and operational patterns (29-36)
    sla_focus_ids = [1003, 1004, 1025, 1033, 1088, 1110, 1143, 1176]
    for idx, issue_id in enumerate(sla_focus_ids, start=29):
        queries.append(
            make_query(
                f"gq-{idx:03d}",
                f"Analyze SLA behavior around issue #{issue_id} "
                "and identify breach/near-breach indicators.",
                "sla_analysis",
                [
                    issue(issue_id),
                    wiki(f"SLA-Metrics-Guide-{(idx % 20) + 1}"),
                    news(91100 + (idx % 15)),
                    message(96000 + ((idx % 12) * 2)),
                ],
                difficulty="advanced",
                tags=["sla", "time-pattern", "operations"],
                language="en",
            )
        )

    # Knowledge and communication centric questions (37-44)
    knowledge_specs = [
        (
            "gq-037",
            "Které wiki a dokumenty nejlépe vysvětlují citation quality proces?",
            "Citation-Quality-Checklist-5",
            92101,
            91102,
            96008,
        ),
        (
            "gq-038",
            "Summarize incident review narrative across news, documents, and ops threads.",
            "Root-Cause-Catalog-3",
            92105,
            91104,
            96010,
        ),
        (
            "gq-039",
            "Jak se promítla architecture decision do operativních threadů?",
            "Evidence-Timeline-FAQ-2",
            92107,
            91103,
            96000,
        ),
        (
            "gq-040",
            "What sources justify process changes in support workflow calibration?",
            "Escalation-Policy-4",
            92109,
            91102,
            96014,
        ),
        (
            "gq-041",
            "Najdi podklady pro release readiness a rollback governance.",
            "SLA-Metrics-Guide-1",
            92100,
            91100,
            95001,
        ),
        (
            "gq-042",
            "Which communication threads document decision points for module tradeoffs?",
            "Evidence-Timeline-FAQ-7",
            92111,
            91106,
            96006,
        ),
        (
            "gq-043",
            "Kde je vidět propojení files -> wiki -> documents u evidence chain?",
            "Reporting-Citations",
            92002,
            91107,
            96012,
        ),
        (
            "gq-044",
            "Provide a grounded communication summary for architecture vs ops follow-ups.",
            "Citation-Quality-Checklist-10",
            92113,
            91108,
            96018,
        ),
    ]
    for query_id, text, wiki_title, doc_id, news_id, message_id in knowledge_specs:
        queries.append(
            make_query(
                query_id,
                text,
                "communication_summary",
                [wiki(wiki_title), document(doc_id), news(news_id), message(message_id)],
                difficulty="basic",
                tags=["knowledge", "communication", "cross-source"],
                language="en" if query_id in {"gq-038", "gq-040", "gq-042", "gq-044"} else "cs",
            )
        )

    # Noisy-data robustness scenarios (45-50)
    noisy_issue_ids = [1000, 1017, 1038, 1052, 1078, 1114]
    noisy_wiki_titles = [
        "SLA-Metrics-Guide-6",
        "Evidence-Timeline-FAQ-7",
        "Root-Cause-Catalog-8",
        "Escalation-Policy-9",
        "Citation-Quality-Checklist-10",
        "SLA-Metrics-Guide-11",
    ]
    for offset, issue_id in enumerate(noisy_issue_ids, start=45):
        queries.append(
            make_query(
                f"gq-{offset:03d}",
                f"Pracuj s noisy daty kolem issue #{issue_id}: odděl fakta od šumu a cituj zdroje.",
                "data_quality_audit",
                [
                    issue(issue_id),
                    wiki(noisy_wiki_titles[offset - 45]),
                    document(92100 + ((offset + 3) % 18)),
                    message(96000 + (((offset + 1) % 12) * 2)),
                ],
                difficulty="advanced",
                tags=["noise", "robustness", "groundedness"],
            )
        )

    assert 40 <= len(queries) <= 80
    return queries


def write_queries(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def main() -> None:
    rows = build_queries()
    write_queries(OUTPUT_PATH, rows)
    print(f"Wrote {len(rows)} golden queries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
