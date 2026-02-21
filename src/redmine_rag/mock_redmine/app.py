from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from redmine_rag.mock_redmine.fixtures import (
    BOARDS,
    DOCUMENTS,
    FILES,
    GROUPS,
    ISSUE_PRIORITIES,
    ISSUE_STATUSES,
    ISSUES,
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
WIKI_PAGE_BY_PROJECT_AND_TITLE = {
    (page["project_id"], page["title"].lower()): page for page in WIKI_PAGES
}

PROJECTS_SORTED = tuple(sorted(PROJECTS, key=lambda project: int(project["id"])))
USERS_SORTED = tuple(sorted(USERS, key=lambda user: int(user["id"])))
GROUPS_SORTED = tuple(sorted(GROUPS, key=lambda group: int(group["id"])))
ISSUES_SORTED = tuple(sorted(ISSUES, key=lambda issue: int(issue["id"])))
TIME_ENTRIES_SORTED = tuple(sorted(TIME_ENTRIES, key=lambda entry: int(entry["id"])))
NEWS_SORTED = tuple(sorted(NEWS, key=lambda entry: int(entry["id"])))
DOCUMENTS_SORTED = tuple(sorted(DOCUMENTS, key=lambda entry: int(entry["id"])))
FILES_SORTED = tuple(sorted(FILES, key=lambda entry: int(entry["id"])))

_topics_by_board_id: dict[int, list[dict[str, Any]]] = defaultdict(list)
_replies_by_parent_id: dict[int, list[dict[str, Any]]] = defaultdict(list)
for message in MESSAGES:
    parent_id = message["parent_id"]
    if parent_id is None:
        _topics_by_board_id[message["board_id"]].append(message)
        continue
    _replies_by_parent_id[parent_id].append(message)

TOPICS_BY_BOARD_ID = {
    board_id: tuple(sorted(items, key=lambda item: int(item["id"])))
    for board_id, items in _topics_by_board_id.items()
}
REPLIES_BY_PARENT_ID = {
    parent_id: tuple(sorted(items, key=lambda item: int(item["id"])))
    for parent_id, items in _replies_by_parent_id.items()
}


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


def _collect_page(
    items: Iterable[dict[str, Any]],
    *,
    offset: int,
    limit: int,
    predicate: Callable[[dict[str, Any]], bool] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    page: list[dict[str, Any]] = []
    total_count = 0
    page_end = offset + limit

    for item in items:
        if predicate is not None and not predicate(item):
            continue
        if offset <= total_count < page_end:
            page.append(item)
        total_count += 1

    return page, total_count


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


def _is_issue_visible(issue: dict[str, Any], auth: AuthContext) -> bool:
    if not _is_project_visible(issue["project_id"], auth):
        return False
    if issue.get("is_private", False) and not auth.can_access_private:
        return False
    return True


def _issue_visibility_or_403(issue: dict[str, Any], auth: AuthContext) -> None:
    if not _is_project_visible(issue["project_id"], auth):
        _project_visibility_or_403(issue["project_id"], auth)
    if issue.get("is_private", False) and not auth.can_access_private:
        raise HTTPException(status_code=403, detail="Forbidden")


def _board_visibility_or_403(board: dict[str, Any], auth: AuthContext) -> None:
    _project_visibility_or_403(board["project_id"], auth)
    if board.get("is_private", False) and not auth.can_access_private:
        raise HTTPException(status_code=403, detail="Forbidden")


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
    total_count: int,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    return {
        key: items,
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
    }


@app.get("/projects.json")
def list_projects(
    auth: AuthContext = Depends(get_auth_context),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    projects_page, total_count = _collect_page(
        PROJECTS_SORTED,
        offset=offset,
        limit=limit,
        predicate=lambda project: _is_project_visible(project["id"], auth),
    )
    return _paginate_response("projects", projects_page, total_count, limit, offset)


@app.get("/users.json")
def list_users(
    _: AuthContext = Depends(get_auth_context),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    users_page, total_count = _collect_page(USERS_SORTED, offset=offset, limit=limit)
    return _paginate_response("users", users_page, total_count, limit, offset)


@app.get("/groups.json")
def list_groups(
    _: AuthContext = Depends(get_auth_context),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    groups_payload = [
        {
            "id": group["id"],
            "name": group["name"],
            "users": [
                user_ref
                for user_ref in (_user_ref(user_id) for user_id in group["user_ids"])
                if user_ref is not None
            ],
        }
        for group in GROUPS_SORTED
    ]
    groups_page, total_count = _collect_page(groups_payload, offset=offset, limit=limit)
    return _paginate_response("groups", groups_page, total_count, limit, offset)


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

    def _issue_matches(issue: dict[str, Any]) -> bool:
        if project_ids is not None and issue["project_id"] not in project_ids:
            return False
        if not _is_issue_visible(issue, auth):
            return False
        return _matches_updated_filter(issue["updated_on"], updated_filter)

    issues_page, total_count = _collect_page(
        ISSUES_SORTED,
        offset=offset,
        limit=limit,
        predicate=_issue_matches,
    )
    payload = [_serialize_issue(issue, include_fields=include_fields) for issue in issues_page]
    return _paginate_response("issues", payload, total_count, limit, offset)


@app.get("/issues/{issue_id}.json")
def issue_detail(
    issue_id: int,
    include: str | None = Query(default=None),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    issue = ISSUE_BY_ID.get(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Not found")

    _issue_visibility_or_403(issue, auth)
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

    def _time_entry_matches(entry: dict[str, Any]) -> bool:
        if project_ids is not None and entry["project_id"] not in project_ids:
            return False
        if not _is_project_visible(entry["project_id"], auth):
            return False
        return _matches_updated_filter(entry["updated_on"], updated_filter)

    time_entries_page, total_count = _collect_page(
        TIME_ENTRIES_SORTED,
        offset=offset,
        limit=limit,
        predicate=_time_entry_matches,
    )
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
        for entry in time_entries_page
    ]

    return _paginate_response("time_entries", payload, total_count, limit, offset)


@app.get("/news.json")
def list_news(
    project_id: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)

    def _news_matches(entry: dict[str, Any]) -> bool:
        if project_ids is not None and entry["project_id"] not in project_ids:
            return False
        return _is_project_visible(entry["project_id"], auth)

    news_page, total_count = _collect_page(
        NEWS_SORTED,
        offset=offset,
        limit=limit,
        predicate=_news_matches,
    )
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
        for entry in news_page
    ]
    return _paginate_response("news", payload, total_count, limit, offset)


@app.get("/documents.json")
def list_documents(
    project_id: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)

    def _document_matches(entry: dict[str, Any]) -> bool:
        if project_ids is not None and entry["project_id"] not in project_ids:
            return False
        return _is_project_visible(entry["project_id"], auth)

    documents_page, total_count = _collect_page(
        DOCUMENTS_SORTED,
        offset=offset,
        limit=limit,
        predicate=_document_matches,
    )
    payload = [
        {
            "id": entry["id"],
            "project": _project_ref(entry["project_id"]),
            "category": {"id": entry["category_id"], "name": f"Category {entry['category_id']}"},
            "title": entry["title"],
            "description": entry["description"],
            "created_on": entry["created_on"],
        }
        for entry in documents_page
    ]

    return _paginate_response("documents", payload, total_count, limit, offset)


@app.get("/files.json")
def list_files(
    project_id: str | None = Query(default=None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    project_ids = _parse_project_ids(project_id)

    def _file_matches(entry: dict[str, Any]) -> bool:
        if project_ids is not None and entry["project_id"] not in project_ids:
            return False
        return _is_project_visible(entry["project_id"], auth)

    files_page, total_count = _collect_page(
        FILES_SORTED,
        offset=offset,
        limit=limit,
        predicate=_file_matches,
    )
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
        for entry in files_page
    ]

    return _paginate_response("files", payload, total_count, limit, offset)


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

    _board_visibility_or_403(board, auth)
    topics, total_count = _collect_page(
        TOPICS_BY_BOARD_ID.get(board_id, ()),
        offset=offset,
        limit=limit,
    )
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

    return _paginate_response("messages", payload, total_count, limit, offset)


@app.get("/messages/{message_id}.json")
def message_detail(
    message_id: int,
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    message = MESSAGE_BY_ID.get(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Not found")

    board = BOARD_BY_ID.get(message["board_id"])
    if board is None:
        raise HTTPException(status_code=404, detail="Not found")
    _board_visibility_or_403(board, auth)
    replies = [
        {
            "id": reply["id"],
            "subject": reply["subject"],
            "author": _user_ref(reply["author_id"]),
            "created_on": reply["created_on"],
            "updated_on": reply["updated_on"],
            "content": reply["content"],
        }
        for reply in REPLIES_BY_PARENT_ID.get(message_id, ())
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
    page = WIKI_PAGE_BY_PROJECT_AND_TITLE.get((project["id"], title.lower()))
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
