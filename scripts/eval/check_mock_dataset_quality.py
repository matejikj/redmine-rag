from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROFILE_ORDER = ["small", "medium", "large"]
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _load_fixtures(profile: str):
    os.environ["MOCK_REDMINE_DATASET_PROFILE"] = profile
    sys.modules.pop("redmine_rag.mock_redmine.fixtures", None)
    return importlib.import_module("redmine_rag.mock_redmine.fixtures")


def _custom_field(issue: dict[str, Any], name: str, default: Any = None) -> Any:
    for field in issue.get("custom_fields", []):
        if field.get("name") == name:
            return field.get("value")
    return default


def _validate_profile(profile: str) -> tuple[dict[str, Any], list[str]]:
    fx = _load_fixtures(profile)

    issues = list(fx.ISSUES)
    bulk_issues = [issue for issue in issues if issue["id"] >= 1000]
    time_entries = list(fx.TIME_ENTRIES)
    wiki_pages = list(fx.WIKI_PAGES)
    news = list(fx.NEWS)
    documents = list(fx.DOCUMENTS)
    files = list(fx.FILES)
    boards = list(fx.BOARDS)
    messages = list(fx.MESSAGES)

    issue_ids = {issue["id"] for issue in issues}
    user_ids = {user["id"] for user in fx.USERS}

    errors: list[str] = []

    expected_counts = {
        "issues_total": 5 + int(fx.PROFILE_SETTINGS["bulk_issues"]),
        "wiki_total": 3 + int(fx.PROFILE_SETTINGS["bulk_wiki_pages"]),
        "news_total": 2 + int(fx.PROFILE_SETTINGS["bulk_news"]),
        "documents_total": 2 + int(fx.PROFILE_SETTINGS["bulk_documents"]),
        "files_total": 1 + int(fx.PROFILE_SETTINGS["bulk_files"]),
        "messages_total": 4 + int(fx.PROFILE_SETTINGS["bulk_ops_topics"]) * 2,
        "boards_total": 3,
    }

    observed_counts = {
        "issues_total": len(issues),
        "wiki_total": len(wiki_pages),
        "news_total": len(news),
        "documents_total": len(documents),
        "files_total": len(files),
        "messages_total": len(messages),
        "boards_total": len(boards),
        "time_entries_total": len(time_entries),
    }

    for key, expected in expected_counts.items():
        observed = observed_counts[key]
        if observed != expected:
            errors.append(
                f"{profile}: count mismatch for {key}: expected {expected}, got {observed}"
            )

    if len(bulk_issues) != int(fx.PROFILE_SETTINGS["bulk_issues"]):
        expected_bulk_issues = int(fx.PROFILE_SETTINGS["bulk_issues"])
        errors.append(
            f"{profile}: bulk issue count mismatch expected {expected_bulk_issues} "
            f"got {len(bulk_issues)}"
        )

    if len({issue["id"] for issue in issues}) != len(issues):
        errors.append(f"{profile}: duplicate issue ids detected")

    classes = {_custom_field(issue, "Issue Class") for issue in bulk_issues}
    required_classes = {"Epic", "Feature", "Bug", "Support", "Incident"}
    if not required_classes.issubset(classes):
        errors.append(f"{profile}: missing issue classes {sorted(required_classes - classes)}")

    statuses = {issue["status_id"] for issue in bulk_issues}
    if not {1, 2, 3, 4, 5}.issubset(statuses):
        errors.append(f"{profile}: missing status ids {sorted({1, 2, 3, 4, 5} - statuses)}")

    relation_types = {
        relation["relation_type"]
        for issue in bulk_issues
        for relation in issue.get("relations", [])
    }
    if not {"blocks", "relates", "duplicates"}.issubset(relation_types):
        missing_relation_types = sorted({"blocks", "relates", "duplicates"} - relation_types)
        errors.append(f"{profile}: relation type coverage incomplete {missing_relation_types}")

    for issue in issues:
        for relation in issue.get("relations", []):
            if int(relation["issue_id"]) not in issue_ids:
                errors.append(
                    f"{profile}: issue {issue['id']} relation points to missing issue "
                    f"{relation['issue_id']}"
                )

    for entry in time_entries:
        if int(entry["issue_id"]) not in issue_ids:
            errors.append(
                f"{profile}: time entry {entry['id']} points to missing issue {entry['issue_id']}"
            )
        if int(entry["user_id"]) not in user_ids:
            errors.append(
                f"{profile}: time entry {entry['id']} points to missing user {entry['user_id']}"
            )

    for issue in bulk_issues:
        if _custom_field(issue, "Data Quality Flag") is None:
            errors.append(f"{profile}: issue {issue['id']} missing Data Quality Flag")

    data_quality_flags = [
        str(_custom_field(issue, "Data Quality Flag", "Clean")) for issue in bulk_issues
    ]
    noisy_count = sum(flag != "Clean" for flag in data_quality_flags)
    min_noisy = max(10, len(bulk_issues) // 12)
    if noisy_count < min_noisy:
        errors.append(f"{profile}: noisy issue coverage too low {noisy_count} < {min_noisy}")

    missing_workflow_stage = sum(
        _custom_field(issue, "Workflow Stage") is None for issue in bulk_issues
    )
    if missing_workflow_stage < 1:
        errors.append(f"{profile}: expected at least one issue missing Workflow Stage")

    risk_counter = Counter(str(_custom_field(issue, "Risk Flag", "None")) for issue in bulk_issues)
    for required_risk in ("Reopened", "Stalled", "Mis-prioritized"):
        if risk_counter[required_risk] < 1:
            errors.append(f"{profile}: missing risk flag coverage for {required_risk}")

    private_issues = [issue for issue in issues if issue.get("is_private")]
    if not private_issues:
        errors.append(f"{profile}: expected private issues")
    for issue in private_issues:
        if not any(journal.get("private_notes") for journal in issue.get("journals", [])):
            errors.append(f"{profile}: private issue {issue['id']} lacks private journal")

    board_by_id = {board["id"]: board for board in boards}
    if 94002 not in board_by_id or not board_by_id[94002].get("is_private"):
        errors.append(f"{profile}: security board 94002 missing or not private")

    for message in messages:
        board_id = int(message["board_id"])
        if board_id not in board_by_id:
            errors.append(f"{profile}: message {message['id']} points to missing board {board_id}")
        if int(message["author_id"]) not in user_ids:
            errors.append(
                f"{profile}: message {message['id']} points to missing user {message['author_id']}"
            )

    observed_counts.update(
        {
            "bulk_issues": len(bulk_issues),
            "noisy_issues": noisy_count,
            "missing_workflow_stage": missing_workflow_stage,
            "risk_flag_counts": dict(risk_counter),
            "relation_type_counts": dict(
                Counter(
                    relation["relation_type"]
                    for issue in bulk_issues
                    for relation in issue.get("relations", [])
                )
            ),
        }
    )

    return observed_counts, errors


def _run_single_profile(profile: str, json_output: bool) -> int:
    summary, errors = _validate_profile(profile)
    payload = {"profile": profile, "summary": summary, "errors": errors}
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Dataset quality summary ({profile}):")
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        if errors:
            print("Errors:")
            for error in errors:
                print(f"- {error}")
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate mock dataset quality constraints")
    parser.add_argument("--profile", choices=PROFILE_ORDER, default="large")
    parser.add_argument("--all-profiles", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    profiles = PROFILE_ORDER if args.all_profiles else [args.profile]
    exit_codes = [_run_single_profile(profile, json_output=args.json) for profile in profiles]
    if any(code != 0 for code in exit_codes):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
