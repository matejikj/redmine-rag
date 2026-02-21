from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any, Iterable

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from redmine_rag.mock_redmine.fixtures import (
    BOARDS,
    DOCUMENTS,
    FILES,
    GROUPS,
    ISSUES,
    ISSUE_PRIORITIES,
    ISSUE_STATUSES,
    MESSAGES,
    NEWS,
    PROJECTS,
    TIME_ENTRIES,
    TRACKERS,
    USERS,
    WIKI_PAGES,
)

app = FastAPI(title="mock-redmine", version="1.0.0")

PROJECT_BY_ID = {project["id"]: project for project in PROJECTS}
PROJECT_BY_IDENTIFIER = {project["identifier"]: project for project in PROJECTS}
USER_BY_ID = {user["id"]: user for user in USERS}
TRACKER_BY_ID = {tracker["id"]: tracker for tracker in TRACKERS}
STATUS_BY_ID = {status["id"]: status for status in ISSUE_STATUSES}
PRIORITY_BY_ID = {priority["id"]: priority for priority in ISSUE_PRIORITIES}
ISSUE_BY_ID = {issue["id"]: issue for issue in ISSUES}
BOARD_BY_ID = {board["id"]: board for board in BOARDS}
MESSAGE_BY_ID = {message["id"]: message for message in MESSAGES}


@dataclass(frozen=True)
class AuthContext:
    can_access_private: bool


def get_auth_context(
    x_redmine_api_key: str | None = Header(default=None, alias="X-Redmine-API-Key"),
    x_mock_role: str | None = Header(default=None, alias="X-Mock-Role"),
) -> AuthContext:
    expected_key = os.getenv("MOCK_REDMINE_API_KEY", "mock-api-key")
    if x_redmine_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return AuthContext(can_access_private=(x_mock_role == "admin"))


def _user_ref(user_id: int | None) -> dict[str, Any] | None:
    if user_id is None:
        return None
    user = USER_BY_ID.get(user_id)
    if user is None:
        return None
    return {"id": user["id"], "name": f"{user['firstname']} {user['lastname']}"}


def _project_ref(project_id: int) -> dict[str, Any]:
    project = PROJECT_BY_ID[project_id]
    return {"id": project["id"], "name": project["name"]}


def _parse_updated_filter(value: str | None) -> tuple[str, datetime] | None:
    if value is None or not value.strip():
        return None

    raw = value.strip()
    for operator in (">=", "<=", ">", "<", "="):
        if raw.startswith(operator):
            timestamp = raw[len(operator) :].strip()
            return operator, _parse_datetime(timestamp)

    return "=", _parse_datetime(raw)


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    if "T" not in normalized:
        normalized = f"{normalized}T00:00:00+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid updated_on value") from exc


def _matches_updated_filter(
    item_updated_on: str | None,
    filter_expr: tuple[str, datetime] | None,
) -> bool:
    if filter_expr is None:
        return True
    if item_updated_on is None:
        return False

    operator, filter_dt = filter_expr
    item_dt = _parse_datetime(item_updated_on)

    if operator == ">=":
        return item_dt >= filter_dt
    if operator == "<=":
        return item_dt <= filter_dt
    if operator == ">":
        return item_dt > filter_dt
    if operator == "<":
        return item_dt < filter_dt
    return item_dt == filter_dt


def _parse_project_ids(project_ids_raw: str | None) -> set[int] | None:
    if project_ids_raw is None or not project_ids_raw.strip():
        return None

    parsed: set[int] = set()
    for token in project_ids_raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            parsed.add(int(token))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid project_id filter") from exc
    return parsed


def _paginate(
    items: list[dict[str, Any]],
    offset: int,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    total_count = len(items)
    return items[offset : offset + limit], total_count


def _is_project_visible(project_id: int, auth: AuthContext) -> bool:
    project = PROJECT_BY_ID.get(project_id)
    if project is None:
        return False
    if not project["is_public"] and not auth.can_access_private:
        return False
    return True


def _project_visibility_or_403(project_id: int, auth: AuthContext) -> None:
    if not _is_project_visible(project_id, auth):
        if project_id in PROJECT_BY_ID:
            raise HTTPException(status_code=403, detail="Forbidden")
        raise HTTPException(status_code=404, detail="Not found")


def _parse_includes(include_raw: str | None) -> set[str]:
    if include_raw is None or not include_raw.strip():
        return set()
    return {item.strip() for item in include_raw.split(",") if item.strip()}


def _serialize_attachment(attachment: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": attachment["id"],
        "filename": attachment["filename"],
        "filesize": attachment["filesize"],
        "content_type": attachment["content_type"],
        "description": attachment["description"],
        "content_url": attachment["content_url"],
        "downloads": attachment["downloads"],
        "author": _user_ref(attachment["author_id"]),
        "created_on": attachment["created_on"],
        "digest": attachment["digest"],
    }


def _serialize_issue(issue: dict[str, Any], include_fields: set[str]) -> dict[str, Any]:
    payload = {
        "id": issue["id"],
        "project": _project_ref(issue["project_id"]),
        "tracker": {
            "id": issue["tracker_id"],
            "name": TRACKER_BY_ID[issue["tracker_id"]]["name"],
        },
        "status": {
            "id": issue["status_id"],
            "name": STATUS_BY_ID[issue["status_id"]]["name"],
        },
        "priority": {
            "id": issue["priority_id"],
            "name": PRIORITY_BY_ID[issue["priority_id"]]["name"],
        },
        "author": _user_ref(issue["author_id"]),
        "assigned_to": _user_ref(issue["assigned_to_id"]),
        "subject": issue["subject"],
        "description": issue["description"],
        "start_date": issue["start_date"],
        "due_date": issue["due_date"],
        "done_ratio": issue["done_ratio"],
        "is_private": issue["is_private"],
        "estimated_hours": issue["estimated_hours"],
        "spent_hours": issue["spent_hours"],
        "created_on": issue["created_on"],
        "updated_on": issue["updated_on"],
        "closed_on": issue["closed_on"],
        "custom_fields": issue["custom_fields"],
    }

    if "journals" in include_fields:
        payload["journals"] = [
            {
                "id": journal["id"],
                "user": _user_ref(journal["user_id"]),
                "notes": journal["notes"],
                "private_notes": journal["private_notes"],
                "created_on": journal["created_on"],
                "details": journal["details"],
            }
            for journal in issue["journals"]
        ]

    if "attachments" in include_fields:
        payload["attachments"] = [
            _serialize_attachment(attachment) for attachment in issue["attachments"]
        ]

    if "relations" in include_fields:
        payload["relations"] = list(issue["relations"])

    if "watchers" in include_fields:
        payload["watchers"] = [
            user_ref
            for user_ref in (_user_ref(user_id) for user_id in issue["watcher_user_ids"])
            if user_ref
        ]

    if "children" in include_fields:
        payload["children"] = [
            {
                "id": child["id"],
                "subject": child["subject"],
                "tracker": {
                    "id": child["tracker_id"],
                    "name": TRACKER_BY_ID[child["tracker_id"]]["name"],
                },
                "status": {
                    "id": child["status_id"],
                    "name": STATUS_BY_ID[child["status_id"]]["name"],
                },
                "priority": {
                    "id": child["priority_id"],
                    "name": PRIORITY_BY_ID[child["priority_id"]]["name"],
                },
            }
            for child_id in issue["child_ids"]
            if (child := ISSUE_BY_ID.get(child_id)) is not None
        ]

    return payload


def _paginate_response(
    key: str,
    items: list[dict[str, Any]],
    limit: int,
    offset: int,
) -> dict[str, Any]:
    page, total_count = _paginate(items, offset=offset, limit=limit)
    return {
        key: page,
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
    }


def _filter_visible_project_items(
    items: Iterable[dict[str, Any]],
    auth: AuthContext,
    project_ids: set[int] | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        project_id = item["project_id"]
        if project_ids is not None and project_id not in project_ids:
            continue
        if not _is_project_visible(project_id, auth):
            continue
        result.append(item)
    return result


@app.get("/projects.json")
def list_projects(
    auth: AuthContext = Depends(get_auth_context),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    visible_projects = [project for project in PROJECTS if _is_project_visible(project["id"], auth)]
    visible_projects.sort(key=lambda project: project["id"])
    return _paginate_response("projects", visible_projects, limit, offset)


@app.get("/users.json")
def list_users(
    _: AuthContext = Depends(get_auth_context),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    users = sorted(USERS, key=lambda user: user["id"])
    return _paginate_response("users", users, limit, offset)


@app.get("/groups.json")
def list_groups(
    _: AuthContext = Depends(get_auth_context),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    groups = [
        {
            "id": group["id"],
            "name": group["name"],
            "users": [
                user_ref
                for user_ref in (_user_ref(user_id) for user_id in group["user_ids"])
                if user_ref is not None
            ],
        }
        for group in sorted(GROUPS, key=lambda entry: entry["id"])
    ]
    return _paginate_response("groups", groups, limit, offset)


@app.get("/trackers.json")
def list_trackers(_: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    return {"trackers": TRACKERS}


@app.get("/issue_statuses.json")
def list_issue_statuses(_: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    return {"issue_statuses": ISSUE_STATUSES}


@app.get("/enumerations/issue_priorities.json")
def list_issue_priorities(_: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    return {"issue_priorities": ISSUE_PRIORITIES}


@app.get("/issues.json")
def list_issues(
    project_id: str | None = Query(default=None),
    include: str | None = Query(default=None),
    updated_on: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)
    updated_filter = _parse_updated_filter(updated_on)
    include_fields = _parse_includes(include)

    filtered = _filter_visible_project_items(ISSUES, auth, project_ids=project_ids)
    filtered = [
        issue for issue in filtered if _matches_updated_filter(issue["updated_on"], updated_filter)
    ]
    filtered.sort(key=lambda issue: issue["id"])

    serialized = [_serialize_issue(issue, include_fields=include_fields) for issue in filtered]
    return _paginate_response("issues", serialized, limit, offset)


@app.get("/issues/{issue_id}.json")
def issue_detail(
    issue_id: int,
    include: str | None = Query(default=None),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    issue = ISSUE_BY_ID.get(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Not found")

    _project_visibility_or_403(issue["project_id"], auth)
    include_fields = _parse_includes(include)
    return {"issue": _serialize_issue(issue, include_fields=include_fields)}


@app.get("/time_entries.json")
def list_time_entries(
    project_id: str | None = Query(default=None),
    updated_on: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)
    updated_filter = _parse_updated_filter(updated_on)

    filtered = _filter_visible_project_items(TIME_ENTRIES, auth, project_ids=project_ids)
    filtered = [
        entry for entry in filtered if _matches_updated_filter(entry["updated_on"], updated_filter)
    ]
    filtered.sort(key=lambda entry: entry["id"])

    payload = [
        {
            "id": entry["id"],
            "project": _project_ref(entry["project_id"]),
            "issue": {"id": entry["issue_id"]} if entry["issue_id"] else None,
            "user": _user_ref(entry["user_id"]),
            "activity": entry["activity"],
            "hours": entry["hours"],
            "comments": entry["comments"],
            "spent_on": entry["spent_on"],
            "created_on": entry["created_on"],
            "updated_on": entry["updated_on"],
        }
        for entry in filtered
    ]

    return _paginate_response("time_entries", payload, limit, offset)


@app.get("/news.json")
def list_news(
    project_id: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)
    filtered = _filter_visible_project_items(NEWS, auth, project_ids=project_ids)
    filtered.sort(key=lambda entry: entry["id"])

    payload = [
        {
            "id": entry["id"],
            "project": _project_ref(entry["project_id"]),
            "title": entry["title"],
            "summary": entry["summary"],
            "description": entry["description"],
            "author": _user_ref(entry["author_id"]),
            "created_on": entry["created_on"],
        }
        for entry in filtered
    ]
    return _paginate_response("news", payload, limit, offset)


@app.get("/documents.json")
def list_documents(
    project_id: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)
    filtered = _filter_visible_project_items(DOCUMENTS, auth, project_ids=project_ids)
    filtered.sort(key=lambda entry: entry["id"])

    payload = [
        {
            "id": entry["id"],
            "project": _project_ref(entry["project_id"]),
            "category": {"id": entry["category_id"], "name": f"Category {entry['category_id']}"},
            "title": entry["title"],
            "description": entry["description"],
            "created_on": entry["created_on"],
        }
        for entry in filtered
    ]

    return _paginate_response("documents", payload, limit, offset)


@app.get("/files.json")
def list_files(
    project_id: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)
    filtered = _filter_visible_project_items(FILES, auth, project_ids=project_ids)
    filtered.sort(key=lambda entry: entry["id"])

    payload = [
        {
            "id": entry["id"],
            "project": _project_ref(entry["project_id"]),
            "filename": entry["filename"],
            "filesize": entry["filesize"],
            "content_type": entry["content_type"],
            "description": entry["description"],
            "content_url": entry["content_url"],
            "author": _user_ref(entry["author_id"]),
            "created_on": entry["created_on"],
        }
        for entry in filtered
    ]

    return _paginate_response("files", payload, limit, offset)


@app.get("/boards/{board_id}/topics.json")
def list_board_topics(
    board_id: int,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    board = BOARD_BY_ID.get(board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="Not found")

    _project_visibility_or_403(board["project_id"], auth)

    topics = [
        message
        for message in MESSAGES
        if message["board_id"] == board_id and message["parent_id"] is None
    ]
    topics.sort(key=lambda message: message["id"])

    payload = [
        {
            "id": message["id"],
            "subject": message["subject"],
            "author": _user_ref(message["author_id"]),
            "created_on": message["created_on"],
            "updated_on": message["updated_on"],
            "replies_count": message["replies_count"],
            "last_reply": {"id": message["last_reply_id"]} if message["last_reply_id"] else None,
        }
        for message in topics
    ]

    return _paginate_response("messages", payload, limit, offset)


@app.get("/messages/{message_id}.json")
def message_detail(
    message_id: int,
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    message = MESSAGE_BY_ID.get(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Not found")

    _project_visibility_or_403(message["project_id"], auth)
    replies = [
        {
            "id": reply["id"],
            "subject": reply["subject"],
            "author": _user_ref(reply["author_id"]),
            "created_on": reply["created_on"],
            "updated_on": reply["updated_on"],
            "content": reply["content"],
        }
        for reply in MESSAGES
        if reply["parent_id"] == message_id
    ]

    return {
        "message": {
            "id": message["id"],
            "board": {"id": message["board_id"], "name": BOARD_BY_ID[message["board_id"]]["name"]},
            "subject": message["subject"],
            "author": _user_ref(message["author_id"]),
            "content": message["content"],
            "created_on": message["created_on"],
            "updated_on": message["updated_on"],
            "replies": replies,
            "locked": message["locked"],
            "sticky": message["sticky"],
        }
    }


@app.get("/projects/{project_ref}/wiki/{title}.json")
def wiki_page_detail(
    project_ref: str,
    title: str,
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project = PROJECT_BY_IDENTIFIER.get(project_ref)
    if project is None and project_ref.isdigit():
        project = PROJECT_BY_ID.get(int(project_ref))
    if project is None:
        raise HTTPException(status_code=404, detail="Not found")

    _project_visibility_or_403(project["id"], auth)

    page = next(
        (
            entry
            for entry in WIKI_PAGES
            if entry["project_id"] == project["id"] and entry["title"].lower() == title.lower()
        ),
        None,
    )
    if page is None:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "wiki_page": {
            "title": page["title"],
            "version": page["version"],
            "text": page["text"],
            "author": _user_ref(page["author_id"]),
            "comments": page["comments"],
            "updated_on": page["updated_on"],
            "parent": page["parent"],
        }
    }
