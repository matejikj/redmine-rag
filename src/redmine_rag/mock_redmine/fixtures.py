from __future__ import annotations

import os

PROJECTS = [
    {
        "id": 1,
        "identifier": "platform-core",
        "name": "SupportHub Platform",
        "description": (
            "Unified customer support platform: agent workspace, "
            "knowledge base, SLA automation, and reporting."
        ),
        "status": 1,
        "is_public": True,
        "created_on": "2025-01-10T08:30:00Z",
        "updated_on": "2026-02-19T09:15:00Z",
    },
]

USERS = [
    {
        "id": 1,
        "login": "alice.smith",
        "firstname": "Alice",
        "lastname": "Smith",
        "mail": "alice@example.test",
        "admin": True,
        "status": 1,
        "role": "Tech Lead",
        "seniority": "Principal",
        "competencies": ["Authentication", "Architecture", "Code Review"],
        "created_on": "2024-01-01T09:00:00Z",
        "updated_on": "2026-02-01T09:00:00Z",
    },
    {
        "id": 2,
        "login": "bob.brown",
        "firstname": "Bob",
        "lastname": "Brown",
        "mail": "bob@example.test",
        "admin": False,
        "status": 1,
        "role": "Incident Manager",
        "seniority": "Senior",
        "competencies": ["Escalation", "SLA Management", "Operations"],
        "created_on": "2024-01-15T09:00:00Z",
        "updated_on": "2026-01-30T09:00:00Z",
    },
    {
        "id": 3,
        "login": "carol.davis",
        "firstname": "Carol",
        "lastname": "Davis",
        "mail": "carol@example.test",
        "admin": False,
        "status": 1,
        "role": "Product Owner",
        "seniority": "Senior",
        "competencies": ["Prioritization", "Scope", "Roadmap"],
        "created_on": "2024-02-10T09:00:00Z",
        "updated_on": "2026-01-28T09:00:00Z",
    },
    {
        "id": 4,
        "login": "tomas.bures",
        "firstname": "Tomas",
        "lastname": "Bures",
        "mail": "tomas@example.test",
        "admin": False,
        "status": 1,
        "role": "Support Agent",
        "seniority": "L2",
        "competencies": ["Incident Triage", "Customer Communication"],
        "created_on": "2024-03-01T09:00:00Z",
        "updated_on": "2026-01-25T09:00:00Z",
    },
    {
        "id": 5,
        "login": "lucie.vackova",
        "firstname": "Lucie",
        "lastname": "Vackova",
        "mail": "lucie@example.test",
        "admin": False,
        "status": 1,
        "role": "Support Agent",
        "seniority": "L1",
        "competencies": ["Ticket Intake", "SLA Acknowledgment"],
        "created_on": "2024-03-10T09:00:00Z",
        "updated_on": "2026-01-24T09:00:00Z",
    },
    {
        "id": 6,
        "login": "david.kral",
        "firstname": "David",
        "lastname": "Kral",
        "mail": "david@example.test",
        "admin": False,
        "status": 1,
        "role": "Security Engineer",
        "seniority": "Senior",
        "competencies": ["Threat Modeling", "Token Security", "Compliance"],
        "created_on": "2024-03-20T09:00:00Z",
        "updated_on": "2026-01-23T09:00:00Z",
    },
    {
        "id": 7,
        "login": "klara.sedlakova",
        "firstname": "Klara",
        "lastname": "Sedlakova",
        "mail": "klara@example.test",
        "admin": False,
        "status": 1,
        "role": "Customer Success",
        "seniority": "Lead",
        "competencies": ["Customer Impact", "Escalation Communication"],
        "created_on": "2024-04-01T09:00:00Z",
        "updated_on": "2026-01-22T09:00:00Z",
    },
    {
        "id": 8,
        "login": "ondrej.pesek",
        "firstname": "Ondrej",
        "lastname": "Pesek",
        "mail": "ondrej@example.test",
        "admin": False,
        "status": 1,
        "role": "Data Analyst",
        "seniority": "Senior",
        "competencies": ["Reporting", "Metrics", "Trend Analysis"],
        "created_on": "2024-04-10T09:00:00Z",
        "updated_on": "2026-01-20T09:00:00Z",
    },
    {
        "id": 9,
        "login": "eva.holubova",
        "firstname": "Eva",
        "lastname": "Holubova",
        "mail": "eva@example.test",
        "admin": False,
        "status": 1,
        "role": "QA Engineer",
        "seniority": "Mid",
        "competencies": ["Regression Testing", "Reproduction Quality"],
        "created_on": "2024-05-01T09:00:00Z",
        "updated_on": "2026-01-19T09:00:00Z",
    },
    {
        "id": 10,
        "login": "filip.dvorak",
        "firstname": "Filip",
        "lastname": "Dvorak",
        "mail": "filip@example.test",
        "admin": False,
        "status": 1,
        "role": "SRE",
        "seniority": "Senior",
        "competencies": ["Reliability", "Observability", "Runbooks"],
        "created_on": "2024-05-20T09:00:00Z",
        "updated_on": "2026-01-18T09:00:00Z",
    },
    {
        "id": 11,
        "login": "adam.cerny",
        "firstname": "Adam",
        "lastname": "Cerny",
        "mail": "adam@example.test",
        "admin": False,
        "status": 1,
        "role": "Support Agent",
        "seniority": "L1",
        "competencies": ["Ticket Classification", "Customer Follow-up"],
        "created_on": "2024-06-01T09:00:00Z",
        "updated_on": "2026-01-17T09:00:00Z",
    },
    {
        "id": 12,
        "login": "tereza.sykorova",
        "firstname": "Tereza",
        "lastname": "Sykorova",
        "mail": "tereza@example.test",
        "admin": False,
        "status": 1,
        "role": "Support Agent",
        "seniority": "L2",
        "competencies": ["Escalation Intake", "Root-Cause Follow-up"],
        "created_on": "2024-06-10T09:00:00Z",
        "updated_on": "2026-01-16T09:00:00Z",
    },
    {
        "id": 13,
        "login": "marek.prochazka",
        "firstname": "Marek",
        "lastname": "Prochazka",
        "mail": "marek@example.test",
        "admin": False,
        "status": 1,
        "role": "Backend Engineer",
        "seniority": "Senior",
        "competencies": ["API Design", "Performance", "Auth Integrations"],
        "created_on": "2024-07-01T09:00:00Z",
        "updated_on": "2026-01-15T09:00:00Z",
    },
    {
        "id": 14,
        "login": "nikola.blahova",
        "firstname": "Nikola",
        "lastname": "Blahova",
        "mail": "nikola@example.test",
        "admin": False,
        "status": 1,
        "role": "Knowledge Manager",
        "seniority": "Senior",
        "competencies": ["Knowledge Base", "Documentation Governance"],
        "created_on": "2024-07-15T09:00:00Z",
        "updated_on": "2026-01-14T09:00:00Z",
    },
    {
        "id": 15,
        "login": "roman.kubat",
        "firstname": "Roman",
        "lastname": "Kubat",
        "mail": "roman@example.test",
        "admin": False,
        "status": 1,
        "role": "Incident Commander",
        "seniority": "Lead",
        "competencies": ["Major Incident", "War Room Coordination"],
        "created_on": "2024-08-01T09:00:00Z",
        "updated_on": "2026-01-13T09:00:00Z",
    },
    {
        "id": 16,
        "login": "veronika.melicharova",
        "firstname": "Veronika",
        "lastname": "Melicharova",
        "mail": "veronika@example.test",
        "admin": False,
        "status": 1,
        "role": "Integrations Engineer",
        "seniority": "Mid",
        "competencies": ["Event Pipelines", "Data Contracts"],
        "created_on": "2024-08-20T09:00:00Z",
        "updated_on": "2026-01-12T09:00:00Z",
    },
    {
        "id": 17,
        "login": "jakub.vavra",
        "firstname": "Jakub",
        "lastname": "Vavra",
        "mail": "jakub@example.test",
        "admin": False,
        "status": 1,
        "role": "Release Manager",
        "seniority": "Senior",
        "competencies": ["Release Planning", "Risk Coordination"],
        "created_on": "2024-09-01T09:00:00Z",
        "updated_on": "2026-01-11T09:00:00Z",
    },
    {
        "id": 18,
        "login": "barbora.nemcova",
        "firstname": "Barbora",
        "lastname": "Nemcova",
        "mail": "barbora@example.test",
        "admin": False,
        "status": 1,
        "role": "Security Analyst",
        "seniority": "Mid",
        "competencies": ["Risk Scoring", "Security Evidence"],
        "created_on": "2024-09-15T09:00:00Z",
        "updated_on": "2026-01-10T09:00:00Z",
    },
    {
        "id": 19,
        "login": "michal.benes",
        "firstname": "Michal",
        "lastname": "Benes",
        "mail": "michal@example.test",
        "admin": False,
        "status": 1,
        "role": "Customer Success",
        "seniority": "Mid",
        "competencies": ["Enterprise Accounts", "Customer Escalations"],
        "created_on": "2024-10-01T09:00:00Z",
        "updated_on": "2026-01-09T09:00:00Z",
    },
    {
        "id": 20,
        "login": "simona.rezkova",
        "firstname": "Simona",
        "lastname": "Rezkova",
        "mail": "simona@example.test",
        "admin": False,
        "status": 1,
        "role": "Technical Writer",
        "seniority": "Senior",
        "competencies": ["Runbook Quality", "Knowledge Articles"],
        "created_on": "2024-10-10T09:00:00Z",
        "updated_on": "2026-01-08T09:00:00Z",
    },
]

GROUPS = [
    {"id": 11, "name": "SupportHub Incident Command", "user_ids": [2, 10, 15, 17]},
    {"id": 12, "name": "SupportHub Identity Squad", "user_ids": [1, 6, 13, 18]},
    {"id": 13, "name": "SupportHub SLA Automation", "user_ids": [2, 8, 10, 15]},
    {"id": 14, "name": "SupportHub Timeline & Data", "user_ids": [8, 13, 16, 17]},
    {"id": 15, "name": "SupportHub Knowledge Guild", "user_ids": [14, 19, 20]},
    {"id": 16, "name": "SupportHub Agent Pool", "user_ids": [4, 5, 11, 12]},
    {"id": 17, "name": "SupportHub Product Council", "user_ids": [3, 7, 14, 19]},
]

TRACKERS = [
    {"id": 1, "name": "Bug", "default_status_id": 1, "description": "Defect"},
    {"id": 2, "name": "Feature", "default_status_id": 1, "description": "Feature request"},
    {"id": 3, "name": "Support", "default_status_id": 2, "description": "Support ticket"},
]

ISSUE_STATUSES = [
    {"id": 1, "name": "New", "is_closed": False, "is_default": True},
    {"id": 2, "name": "In Progress", "is_closed": False, "is_default": False},
    {"id": 3, "name": "Resolved", "is_closed": False, "is_default": False},
    {"id": 4, "name": "Reopened", "is_closed": False, "is_default": False},
    {"id": 5, "name": "Closed", "is_closed": True, "is_default": False},
]

ISSUE_PRIORITIES = [
    {"id": 1, "name": "Low", "position": 1, "is_default": False, "active": True},
    {"id": 2, "name": "Normal", "position": 2, "is_default": True, "active": True},
    {"id": 3, "name": "High", "position": 3, "is_default": False, "active": True},
    {"id": 4, "name": "Urgent", "position": 4, "is_default": False, "active": True},
]

ISSUES = [
    {
        "id": 101,
        "project_id": 1,
        "tracker_id": 2,
        "status_id": 2,
        "priority_id": 3,
        "subject": "Agent workspace: unified login and role bootstrap",
        "description": (
            "Implement SSO login for agent workspace with OAuth2 + PKCE and "
            "role bootstrapping from identity claims."
        ),
        "author_id": 1,
        "assigned_to_id": 2,
        "start_date": "2026-01-04",
        "due_date": "2026-02-28",
        "done_ratio": 75,
        "is_private": False,
        "estimated_hours": 24.0,
        "spent_hours": 16.5,
        "created_on": "2026-01-04T10:00:00Z",
        "updated_on": "2026-02-16T11:15:00Z",
        "closed_on": None,
        "custom_fields": [
            {"id": 901, "name": "Module", "value": "Auth"},
            {"id": 902, "name": "Customer Impact", "value": "High"},
        ],
        "journals": [
            {
                "id": 1001,
                "user_id": 2,
                "notes": "Added OAuth scope mapping and fallback to local login.",
                "private_notes": False,
                "created_on": "2026-01-12T13:00:00Z",
                "details": [
                    {
                        "property": "attr",
                        "name": "status_id",
                        "old_value": "1",
                        "new_value": "2",
                    }
                ],
            },
            {
                "id": 1002,
                "user_id": 1,
                "notes": "Security review requested. Add token rotation evidence.",
                "private_notes": True,
                "created_on": "2026-02-10T09:30:00Z",
                "details": [],
            },
        ],
        "attachments": [
            {
                "id": 5001,
                "filename": "sso-sequence.md",
                "filesize": 33800,
                "content_type": "text/markdown",
                "description": "Sequence diagram for SSO login flow",
                "content_url": "http://mock-redmine.local/attachments/5001/sso-sequence.md",
                "downloads": 12,
                "author_id": 2,
                "created_on": "2026-01-12T13:05:00Z",
                "digest": "d41d8cd98f00b204e9800998ecf8427e",
            }
        ],
        "relations": [
            {"id": 7001, "issue_id": 102, "relation_type": "blocks", "delay": None}
        ],
        "watcher_user_ids": [1, 3],
        "child_ids": [103],
    },
    {
        "id": 102,
        "project_id": 1,
        "tracker_id": 1,
        "status_id": 1,
        "priority_id": 4,
        "subject": "Safari callback timeout in workspace login",
        "description": "Safari occasionally times out on OAuth callback route.",
        "author_id": 3,
        "assigned_to_id": 2,
        "start_date": "2026-02-01",
        "due_date": "2026-02-21",
        "done_ratio": 25,
        "is_private": False,
        "estimated_hours": 8.0,
        "spent_hours": 2.0,
        "created_on": "2026-02-01T08:15:00Z",
        "updated_on": "2026-02-20T08:20:00Z",
        "closed_on": None,
        "custom_fields": [{"id": 901, "name": "Module", "value": "Auth"}],
        "journals": [
            {
                "id": 1003,
                "user_id": 2,
                "notes": "Reproduced on Safari 17.4, suspect cookie SameSite mismatch.",
                "private_notes": False,
                "created_on": "2026-02-02T11:00:00Z",
                "details": [],
            }
        ],
        "attachments": [],
        "relations": [{"id": 7002, "issue_id": 101, "relation_type": "blocked", "delay": None}],
        "watcher_user_ids": [1],
        "child_ids": [],
    },
    {
        "id": 103,
        "project_id": 1,
        "tracker_id": 3,
        "status_id": 3,
        "priority_id": 2,
        "subject": "Update incident runbook for auth rollback",
        "description": "Prepare rollback procedure for authentication incidents.",
        "author_id": 1,
        "assigned_to_id": 3,
        "start_date": "2026-02-03",
        "due_date": "2026-02-17",
        "done_ratio": 100,
        "is_private": False,
        "estimated_hours": 3.0,
        "spent_hours": 3.0,
        "created_on": "2026-02-03T09:00:00Z",
        "updated_on": "2026-02-15T18:00:00Z",
        "closed_on": "2026-02-15T18:00:00Z",
        "custom_fields": [{"id": 901, "name": "Module", "value": "Operations"}],
        "journals": [],
        "attachments": [],
        "relations": [],
        "watcher_user_ids": [2, 3],
        "child_ids": [],
    },
    {
        "id": 201,
        "project_id": 1,
        "tracker_id": 2,
        "status_id": 2,
        "priority_id": 2,
        "subject": "Ticket timeline: evidence timeline aggregation",
        "description": (
            "Build timeline aggregation for issue events, comments, and "
            "time entries in a single evidence view."
        ),
        "author_id": 2,
        "assigned_to_id": 3,
        "start_date": "2026-01-20",
        "due_date": "2026-03-05",
        "done_ratio": 55,
        "is_private": False,
        "estimated_hours": 30.0,
        "spent_hours": 10.0,
        "created_on": "2026-01-20T10:30:00Z",
        "updated_on": "2026-02-19T09:45:00Z",
        "closed_on": None,
        "custom_fields": [{"id": 901, "name": "Module", "value": "Sync"}],
        "journals": [
            {
                "id": 2001,
                "user_id": 3,
                "notes": "Event stream now includes status transition provenance.",
                "private_notes": False,
                "created_on": "2026-02-11T12:20:00Z",
                "details": [],
            }
        ],
        "attachments": [],
        "relations": [],
        "watcher_user_ids": [2],
        "child_ids": [],
    },
    {
        "id": 301,
        "project_id": 1,
        "tracker_id": 2,
        "status_id": 1,
        "priority_id": 4,
        "subject": "Private security review: token replay mitigation",
        "description": (
            "Restricted security review for replay mitigation in agent login "
            "and API session refresh."
        ),
        "author_id": 1,
        "assigned_to_id": 6,
        "start_date": "2026-02-01",
        "due_date": "2026-03-15",
        "done_ratio": 20,
        "is_private": True,
        "estimated_hours": 40.0,
        "spent_hours": 6.0,
        "created_on": "2026-02-01T09:00:00Z",
        "updated_on": "2026-02-18T10:10:00Z",
        "closed_on": None,
        "custom_fields": [{"id": 903, "name": "Confidentiality", "value": "Restricted"}],
        "journals": [
            {
                "id": 3001,
                "user_id": 6,
                "notes": "Threat model updated with replay attack scenarios.",
                "private_notes": True,
                "created_on": "2026-02-10T15:00:00Z",
                "details": [],
            }
        ],
        "attachments": [],
        "relations": [],
        "watcher_user_ids": [1, 6, 18],
        "child_ids": [],
    },
]

TIME_ENTRIES = [
    {
        "id": 8101,
        "project_id": 1,
        "issue_id": 101,
        "user_id": 2,
        "activity": {"id": 9, "name": "Development"},
        "hours": 3.5,
        "comments": "Implemented PKCE verifier handling.",
        "spent_on": "2026-02-12",
        "created_on": "2026-02-12T17:00:00Z",
        "updated_on": "2026-02-12T17:00:00Z",
    },
    {
        "id": 8102,
        "project_id": 1,
        "issue_id": 102,
        "user_id": 2,
        "activity": {"id": 10, "name": "QA"},
        "hours": 1.5,
        "comments": "Safari callback diagnostics.",
        "spent_on": "2026-02-14",
        "created_on": "2026-02-14T16:30:00Z",
        "updated_on": "2026-02-14T16:30:00Z",
    },
    {
        "id": 8201,
        "project_id": 1,
        "issue_id": 201,
        "user_id": 3,
        "activity": {"id": 9, "name": "Development"},
        "hours": 4.0,
        "comments": "Evidence timeline aggregation prototype.",
        "spent_on": "2026-02-18",
        "created_on": "2026-02-18T18:00:00Z",
        "updated_on": "2026-02-18T18:00:00Z",
    },
]

WIKI_PAGES = [
    {
        "project_id": 1,
        "project_identifier": "platform-core",
        "title": "Feature-Login",
        "text": "Agent workspace login supports SSO, fallback local auth, and audit logging.",
        "version": 4,
        "author_id": 1,
        "comments": "Revision 4 adds evidence from issues #101 and #102.",
        "updated_on": "2026-02-17T10:00:00Z",
        "parent": None,
    },
    {
        "project_id": 1,
        "project_identifier": "platform-core",
        "title": "Incident-Triage-Playbook",
        "text": (
            "Triage playbook defines severity matrix, first response template, "
            "and escalation ownership. Updated after incident #301 and support issue #1038."
        ),
        "version": 2,
        "author_id": 3,
        "comments": "Revision 2 reflects incident command handoff from issue #301.",
        "updated_on": "2026-02-19T12:30:00Z",
        "parent": None,
    },
    {
        "project_id": 1,
        "project_identifier": "platform-core",
        "title": "Reporting-Citations",
        "text": (
            "Citation rendering describes source mapping for issue comments, "
            "wiki paragraphs, and attachments. Example evidence chain: issue #201 -> wiki paragraph -> file export."
        ),
        "version": 1,
        "author_id": 1,
        "comments": "Initial citation strategy aligned with issue #201.",
        "updated_on": "2026-02-18T12:00:00Z",
        "parent": None,
    },
]

NEWS = [
    {
        "id": 91001,
        "project_id": 1,
        "title": "SupportHub auth hardening milestone",
        "summary": "Completed phase 1 hardening.",
        "description": "PKCE and token rotation controls are now in staging, based on issues #101 and #102.",
        "author_id": 1,
        "created_on": "2026-02-15T08:00:00Z",
    },
    {
        "id": 91002,
        "project_id": 1,
        "title": "Evidence timeline RFC published",
        "summary": "RFC draft available.",
        "description": "Initial RFC for evidence timeline architecture is available with references to issue #201.",
        "author_id": 2,
        "created_on": "2026-02-19T09:00:00Z",
    },
]

DOCUMENTS = [
    {
        "id": 92001,
        "project_id": 1,
        "category_id": 1,
        "title": "SSO rollout checklist",
        "description": "Checklist for rollout and rollback linked to issues #101 and #102.",
        "created_on": "2026-02-13T09:00:00Z",
    },
    {
        "id": 92002,
        "project_id": 1,
        "category_id": 2,
        "title": "Evidence timeline design",
        "description": "Design proposal and edge case matrix using issue #201 as primary scenario.",
        "created_on": "2026-02-19T11:00:00Z",
    },
]

FILES = [
    {
        "id": 93001,
        "project_id": 1,
        "filename": "oauth-audit-template.xlsx",
        "filesize": 9100,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "description": "Audit sheet template for issue #101 rollout evidence.",
        "content_url": "http://mock-redmine.local/files/93001/oauth-audit-template.xlsx",
        "author_id": 1,
        "created_on": "2026-02-14T12:00:00Z",
    }
]

BOARDS = [
    {
        "id": 94001,
        "project_id": 1,
        "name": "Architecture Discussions",
        "description": "Architecture decisions and implementation tradeoffs tied to active issues.",
        "position": 1,
        "is_private": False,
        "topics_count": 2,
        "messages_count": 3,
    },
    {
        "id": 94002,
        "project_id": 1,
        "name": "Security Review Board",
        "description": "Restricted board for security findings and production incident response.",
        "position": 1,
        "is_private": True,
        "topics_count": 1,
        "messages_count": 1,
    },
]

MESSAGES = [
    {
        "id": 95001,
        "board_id": 94001,
        "project_id": 1,
        "parent_id": None,
        "author_id": 1,
        "subject": "OAuth rollout readiness",
        "content": (
            "Please review checklist and monitoring plan for issues #101 and #102. "
            "Decision: rollout proceeds only with document #92001 sign-off and board follow-up."
        ),
        "replies_count": 1,
        "last_reply_id": 95002,
        "locked": False,
        "sticky": 1,
        "created_on": "2026-02-13T12:00:00Z",
        "updated_on": "2026-02-14T12:15:00Z",
    },
    {
        "id": 95002,
        "board_id": 94001,
        "project_id": 1,
        "parent_id": 95001,
        "author_id": 2,
        "subject": "Re: OAuth rollout readiness",
        "content": (
            "Monitoring alerts for callback errors are active; reference file #93001 and issue #102. "
            "Follow-up owner confirmed release checkpoint."
        ),
        "replies_count": 0,
        "last_reply_id": None,
        "locked": False,
        "sticky": 0,
        "created_on": "2026-02-14T12:15:00Z",
        "updated_on": "2026-02-14T12:15:00Z",
    },
    {
        "id": 95003,
        "board_id": 94001,
        "project_id": 1,
        "parent_id": None,
        "author_id": 3,
        "subject": "Safari callback errors",
        "content": (
            "Collected browser logs and timings for issue #102. "
            "Architecture decision pending between cookie policy update and callback retry strategy."
        ),
        "replies_count": 0,
        "last_reply_id": None,
        "locked": False,
        "sticky": 0,
        "created_on": "2026-02-20T08:45:00Z",
        "updated_on": "2026-02-20T08:45:00Z",
    },
    {
        "id": 95999,
        "board_id": 94002,
        "project_id": 1,
        "parent_id": None,
        "author_id": 1,
        "subject": "Replay mitigation threat review",
        "content": (
            "Restricted security findings and mitigations for issue #301 and incident class threads. "
            "Decision: keep evidence trail private; update document #92101 with approved controls."
        ),
        "replies_count": 0,
        "last_reply_id": None,
        "locked": True,
        "sticky": 1,
        "created_on": "2026-02-18T13:00:00Z",
        "updated_on": "2026-02-18T13:00:00Z",
    },
]


def _day_str(base_day: int, offset: int, max_day: int) -> str:
    return f"{((base_day + offset - 1) % max_day) + 1:02d}"


WORKSTREAMS = [
    {
        "name": "Authentication",
        "goal": "stabilize login reliability and role provisioning",
        "modules": ["Auth Gateway", "Session Service", "Role Mapper"],
    },
    {
        "name": "SLA Automation",
        "goal": "enforce first response and resolution targets",
        "modules": ["SLA Engine", "Escalation Router", "Priority Rules"],
    },
    {
        "name": "Evidence Timeline",
        "goal": "unify comments, status changes, and spent time into one timeline",
        "modules": ["Timeline API", "Journal Merger", "Audit Feed"],
    },
    {
        "name": "Knowledge Base",
        "goal": "connect wiki quality with incident resolution speed",
        "modules": ["KB Sync", "Article Scoring", "Gap Detection"],
    },
    {
        "name": "Reporting & Citations",
        "goal": "produce grounded insights with source references",
        "modules": ["Citation Builder", "Insight Export", "Traceability Layer"],
    },
]

CUSTOMER_SEGMENTS = ["SMB", "Mid-market", "Enterprise", "Public Sector"]
CUSTOMER_ACCOUNTS = [
    "Northwind Retail",
    "BlueRail Logistics",
    "CivicLedger",
    "Mercury Utilities",
    "Helios Transit",
    "Riverside Health",
    "Atlas Insurance",
    "Orion Manufacturing",
    "Sterling Bank",
    "Pioneer Telecom",
    "Skylark Education",
    "Arctic Energy",
    "Delta Food Group",
    "Nova Aerospace",
    "Beacon Housing",
    "TerraGov",
    "Summit Travel",
    "Echo Mobility",
    "Vertex Pharma",
    "Harbor Ports",
]
SUPPORT_CHANNELS = ["email", "chat", "phone", "portal"]
REGIONS = ["EU-West", "US-East", "AP-South", "ME-Central"]

CAPABILITY_AREAS = [
    "browser callback reliability",
    "session refresh consistency",
    "role bootstrap synchronization",
    "VIP escalation routing",
    "first-response timer enforcement",
    "SLA breach early warnings",
    "audit timeline reconstruction",
    "journal merge ordering",
    "attachment evidence indexing",
    "knowledge article freshness scoring",
    "runbook recommendation scoring",
    "citation quality checks",
    "incident trend digests",
    "handoff ownership tracking",
    "priority override governance",
    "enterprise tenant isolation",
    "postmortem action closure",
    "alert noise suppression",
    "compliance export reliability",
    "on-call shift continuity",
    "customer impact labelling",
    "duplicate detection quality",
    "release rollback confidence",
    "support queue balancing",
]

FAILURE_SIGNALS = [
    "callback request exceeds timeout budget",
    "token refresh sequence fails after role remap",
    "escalation owner is not persisted after reassignment",
    "SLA warning appears after breach threshold",
    "timeline misses one status transition in incident thread",
    "attachment extractor drops UTF-8 stack trace headers",
    "summary cites stale wiki revision for known workaround",
    "runbook link points to archived response playbook",
    "duplicate incident merge loses customer impact context",
    "priority rule maps enterprise outage to Normal",
    "board thread resolution is not reflected in issue state",
    "postmortem action item has no owner after release cut",
    "monitoring alert does not include tenant context",
    "root-cause note remains private after incident closure",
    "support inbox batches urgent tickets behind low-priority queue",
    "status rollback from Closed to In Progress lacks provenance",
    "hotfix verification comment is missing deployment evidence",
    "retry policy causes delayed response spikes on Monday mornings",
    "customer success handoff omits contractual SLA extension",
    "message reply ordering differs from journal chronology",
]

ROOT_CAUSES = [
    "cookie SameSite policy mismatch between Safari and API gateway",
    "race condition in async role mapper after identity token refresh",
    "legacy escalation rule still active for one enterprise segment",
    "timezone conversion error in SLA warning scheduler",
    "journal event stream deduplicates records by wrong key",
    "evidence parser truncates lines above 8 KB payload size",
    "wiki cache invalidation misses parent-child revision updates",
    "priority mapping model trained on outdated incident taxonomy",
    "deployment webhook retries create out-of-order state writes",
    "manual hotfix bypassed post-release checklist gate",
    "queue partition uses stale tenant shard metadata",
    "message consumer falls behind during nightly report exports",
    "missing ownership fallback when assignee leaves on-call rotation",
    "audit feed serializer strips relation type for duplicates",
    "support macro applies low-impact template to outage cases",
    "board moderation lock hides follow-up resolution details",
]

REMEDIATIONS = [
    "introduce explicit callback deadline metric with per-browser fallback",
    "move role bootstrap to idempotent post-login worker",
    "replace legacy escalation rule with contract-aware policy set",
    "normalize SLA scheduler timestamps to UTC before trigger evaluation",
    "persist timeline sequence numbers from raw journal feed",
    "upgrade evidence extractor to streaming parser with checksum validation",
    "wire wiki revision IDs into citation renderer",
    "publish new priority override playbook and enforce audit trail",
    "serialize deployment events through incident timeline gateway",
    "automate hotfix checklist completion before closure transition",
    "refresh tenant shard metadata on assignment updates",
    "throttle report export consumer to protect realtime channels",
    "enforce assignee fallback to incident commander role",
    "retain relation provenance in audit feed snapshots",
    "add outage guardrail to support response macro selection",
    "mirror board resolution notes into issue journals",
]

PREVENTION_ACTIONS = [
    "weekly browser matrix regression in staging",
    "monthly escalation policy drift review",
    "SLA simulator replay during release candidate phase",
    "timeline integrity check in nightly data pipeline",
    "evidence extraction contract tests on sample attachments",
    "wiki freshness report included in release go/no-go",
    "priority override review with customer success lead",
    "post-incident checklist compliance dashboard",
    "on-call handoff dry-run at shift boundary",
    "duplicate merge quality audit in retrospectives",
]

DETECTION_SOURCES = [
    "customer success escalation call",
    "Grafana reliability board",
    "weekly incident retrospective",
    "synthetic login monitor",
    "support queue audit",
    "post-deploy smoke tests",
    "security review checklist",
    "timeline data integrity check",
]

NOISY_CZ_EN_SNIPPETS = [
    "FYI: zákazník píše, že to po deployi zase nefunguje, pls verify ASAP.",
    "Poznámka: logy jsou half-missing a timestampy jsou trochu off.",
    "Quick check: handoff byl OK-ish, ale RCA zatím není complete.",
    "Status update: workaround běží, ale chybí final potvrzení od supportu.",
]

DOMAIN_SLANG_SNIPPETS = [
    "sev2 ping pong",
    "hotfix train",
    "war-room drift",
    "ticket bounce",
    "runbook gap",
]

LEGACY_ARTIFACT_SNIPPETS = [
    "Legacy note: term 'SEV-A bridge' from 2023 is deprecated but still appears in customer comms.",
    "Historical artifact: old macro 'L2 queue v1' was sunset in 2024-09, yet copied in thread notes.",
    "Legacy mapping 'impact_matrix_v0' is obsolete and kept only for audit traceability.",
]

SCENARIO_FAMILIES = [
    "SLA drift",
    "Escalation loop",
    "Knowledge gap",
    "Evidence mismatch",
    "Security incident",
    "False closure",
]

ISSUE_CLASS_CYCLE = ["Epic", "Feature", "Bug", "Support", "Incident"]
TRACKER_BY_ISSUE_CLASS = {
    "Epic": 2,
    "Feature": 2,
    "Bug": 1,
    "Support": 3,
    "Incident": 3,
}
STATUS_BY_ISSUE_CLASS = {
    "Epic": [1, 2, 2, 3],
    "Feature": [1, 2, 3, 5],
    "Bug": [1, 2, 3, 4, 5],
    "Support": [1, 2, 3, 5],
    "Incident": [2, 3, 4, 5],
}
PRIORITY_BY_ISSUE_CLASS = {
    "Epic": [2, 3],
    "Feature": [2, 3],
    "Bug": [2, 3, 4],
    "Support": [1, 2, 3],
    "Incident": [3, 4],
}
WORKFLOW_STAGE_BY_ISSUE_CLASS = {
    "Epic": "Planning",
    "Feature": "Implementation",
    "Bug": "Verification",
    "Support": "Triage",
    "Incident": "Escalation",
}
IMPACT_BY_ISSUE_CLASS = {
    "Epic": ["Medium", "High"],
    "Feature": ["Medium", "High"],
    "Bug": ["Medium", "High"],
    "Support": ["Low", "Medium", "High"],
    "Incident": ["High"],
}
ESTIMATED_HOURS_BY_ISSUE_CLASS = {
    "Epic": 64.0,
    "Feature": 28.0,
    "Bug": 14.0,
    "Support": 8.0,
    "Incident": 20.0,
}
SUPPORT_AGENT_POOL = [4, 5, 11, 12]
INCIDENT_COMMAND_POOL = [2, 10, 15]

DATASET_PROFILES = {
    "small": {
        "bulk_issues": 120,
        "bulk_wiki_pages": 12,
        "bulk_news": 8,
        "bulk_documents": 10,
        "bulk_files": 12,
        "bulk_ops_topics": 8,
    },
    "medium": {
        "bulk_issues": 170,
        "bulk_wiki_pages": 16,
        "bulk_news": 12,
        "bulk_documents": 14,
        "bulk_files": 18,
        "bulk_ops_topics": 10,
    },
    "large": {
        "bulk_issues": 215,
        "bulk_wiki_pages": 20,
        "bulk_news": 15,
        "bulk_documents": 18,
        "bulk_files": 24,
        "bulk_ops_topics": 12,
    },
}

DATASET_PROFILE = os.getenv("MOCK_REDMINE_DATASET_PROFILE", "large").strip().lower()
if DATASET_PROFILE not in DATASET_PROFILES:
    DATASET_PROFILE = "large"

PROFILE_SETTINGS = DATASET_PROFILES[DATASET_PROFILE]
BULK_ISSUE_COUNT = int(PROFILE_SETTINGS["bulk_issues"])
BULK_WIKI_PAGE_COUNT = int(PROFILE_SETTINGS["bulk_wiki_pages"])
BULK_NEWS_COUNT = int(PROFILE_SETTINGS["bulk_news"])
BULK_DOCUMENT_COUNT = int(PROFILE_SETTINGS["bulk_documents"])
BULK_FILE_COUNT = int(PROFILE_SETTINGS["bulk_files"])
BULK_OPS_TOPIC_COUNT = int(PROFILE_SETTINGS["bulk_ops_topics"])

WORKSTREAM_OWNERSHIP = {
    "Authentication": {
        "author_pool": [3, 1, 13],
        "assignee_pool": [1, 13, 6],
        "watcher_pool": [2, 7, 17, 18],
    },
    "SLA Automation": {
        "author_pool": [3, 2, 8],
        "assignee_pool": [2, 10, 15],
        "watcher_pool": [7, 17, 19, 3],
    },
    "Evidence Timeline": {
        "author_pool": [8, 3, 16],
        "assignee_pool": [13, 16, 10],
        "watcher_pool": [2, 7, 17, 8],
    },
    "Knowledge Base": {
        "author_pool": [14, 20, 3],
        "assignee_pool": [14, 20, 4],
        "watcher_pool": [7, 19, 11, 12],
    },
    "Reporting & Citations": {
        "author_pool": [8, 3, 14],
        "assignee_pool": [8, 16, 17],
        "watcher_pool": [2, 7, 19, 20],
    },
}

SECURITY_REVIEWERS = [6, 18]


def _pick(pool: list[int], index: int, offset: int = 0) -> int:
    return pool[(index + offset) % len(pool)]


def _subject_for_issue(
    issue_class: str,
    capability: str,
    signal: str,
    account: str,
    segment: str,
    issue_id: int,
) -> str:
    short_signal = signal.split(" ", 3)[0:3]
    signal_fragment = " ".join(short_signal)
    if issue_class == "Epic":
        return (
            f"Epic #{issue_id}: {capability} program for {segment} accounts "
            f"({account})"
        )
    if issue_class == "Feature":
        return f"Feature #{issue_id}: improve {capability} after {signal_fragment}"
    if issue_class == "Bug":
        return f"Bug #{issue_id}: {signal} observed on {account}"
    if issue_class == "Support":
        return f"Support #{issue_id}: assist {account} with {capability}"
    return f"Incident #{issue_id}: {signal} impacts {segment} operations"


def _description_for_issue(
    issue_class: str,
    stream: dict[str, object],
    module_name: str,
    capability: str,
    signal: str,
    root_cause: str,
    remediation: str,
    prevention: str,
    detection: str,
    account: str,
    segment: str,
    channel: str,
    region: str,
    scenario_family: str,
    risk_flag: str,
) -> str:
    description = (
        f"{issue_class} within workstream '{stream['name']}' ({stream['goal']}). "
        f"Scope: {capability} in module {module_name}. "
        f"Affected customer: {account} ({segment}, {region}) via {channel}. "
        f"Observed signal: {signal}. Detection source: {detection}. "
        f"Likely root cause: {root_cause}. Planned remediation: {remediation}. "
        f"Prevention action: {prevention}. Scenario family: {scenario_family}."
    )
    if risk_flag == "Stalled":
        description += (
            " Work is currently stalled due to pending vendor evidence export "
            "approval; escalation owner must confirm unblock plan."
        )
    if risk_flag == "Mis-prioritized":
        description += (
            " Priority appears under-estimated against customer impact and "
            "requires explicit product-owner override."
        )
    if risk_flag == "Reopened":
        description += (
            " This record includes a false-closure pattern and must preserve "
            "status transition rationale in journals."
        )
    return description


def _status_progression_for_issue(target_status_id: int, is_reopened_case: bool) -> list[int]:
    if target_status_id == 1:
        return [1]
    if target_status_id == 2:
        return [1, 2]
    if target_status_id == 3:
        return [1, 2, 3]
    if target_status_id == 5:
        return [1, 2, 3, 5]
    if target_status_id == 4 and is_reopened_case:
        return [1, 2, 3, 5, 4]
    if target_status_id == 4:
        return [1, 2, 4]
    return [1, target_status_id]


def _done_ratio_progression(final_done_ratio: int, journal_count: int) -> list[int]:
    if journal_count <= 1:
        return [final_done_ratio]

    progression: list[int] = []
    for idx in range(journal_count):
        if idx == journal_count - 1:
            progression.append(final_done_ratio)
            continue
        value = int(round(final_done_ratio * ((idx + 1) / journal_count)))
        progression.append(max(1, min(value, final_done_ratio)))
    progression[-1] = final_done_ratio
    return progression


def _journal_style_for_index(
    journal_idx: int,
    journal_count: int,
    final_status_id: int,
    is_reopened_case: bool,
) -> str:
    if journal_idx == 0:
        return "operational"
    if journal_idx == 1:
        return "technical"
    if journal_idx == journal_count - 1 and final_status_id in {3, 5}:
        return "postmortem"
    if journal_idx == journal_count - 1 and is_reopened_case:
        return "operational"
    if journal_idx == 2:
        return "decision"
    return "technical"


def _journal_note(
    style: str,
    issue_class: str,
    capability: str,
    signal: str,
    account: str,
    segment: str,
    channel: str,
    region: str,
    root_cause: str,
    remediation: str,
    prevention: str,
    detection: str,
    scenario_family: str,
    module_name: str,
    assigned_to_id: int,
    risk_flag: str,
    journal_idx: int,
    index: int,
    is_reopened_case: bool,
) -> str:
    if style == "operational":
        note = (
            f"Operational update: intake via {channel} from {account} ({segment}, {region}) "
            f"confirmed signal '{signal}'. Support queue tagged module {module_name} and scenario "
            f"family '{scenario_family}'. Current owner ID {assigned_to_id} acknowledged action plan."
        )
        if risk_flag == "Stalled":
            note += " Waiting for external evidence export before next execution step."
        if is_reopened_case and journal_idx > 1:
            note += " Customer reproduced regression after closure, therefore the case is reopened."
        return note

    if style == "technical":
        return (
            f"Technical analysis: investigated {capability} for {issue_class.lower()} flow. "
            f"Root cause hypothesis: {root_cause}. Detection context: {detection}. "
            f"Engineering action: {remediation}."
        )

    if style == "decision":
        decision_rationale = [
            "customer impact takes precedence over implementation convenience",
            "on-call and product owner aligned on mitigation-first approach",
            "timeline evidence indicates ownership handoff is required",
        ][(index + journal_idx) % 3]
        return (
            f"Decision log: selected remediation path '{remediation}'. Rationale: {decision_rationale}. "
            f"Owner {assigned_to_id} commits prevention follow-up '{prevention}' and timeline traceability."
        )

    postmortem_angle = [
        "first response and escalation routing worked as expected",
        "root-cause confirmation required cross-team evidence alignment",
        "knowledge update is necessary to avoid repeat incident",
    ][(index + journal_idx) % 3]
    return (
        f"Postmortem summary: closure candidate reviewed for {account}. Outcome: {postmortem_angle}. "
        f"Confirmed root cause '{root_cause}' and prevention action '{prevention}'."
    )


def _bulk_issue(issue_id: int, index: int) -> dict:
    project_id = 1
    story_index = index // len(ISSUE_CLASS_CYCLE)
    story_position = index % len(ISSUE_CLASS_CYCLE)
    issue_class = ISSUE_CLASS_CYCLE[story_position]
    tracker_id = TRACKER_BY_ISSUE_CLASS[issue_class]
    status_options = STATUS_BY_ISSUE_CLASS[issue_class]
    priority_options = PRIORITY_BY_ISSUE_CLASS[issue_class]
    status_id = status_options[(story_index + index) % len(status_options)]
    base_priority_id = priority_options[(story_index + (index * 2)) % len(priority_options)]
    priority_id = base_priority_id
    created_day = _day_str(1, index, 28)
    updated_day = _day_str(1, index, 18)  # Keep under 2026-02-19 for existing tests.
    due_day = _day_str(5, index + story_position, 28)
    stream = WORKSTREAMS[index % len(WORKSTREAMS)]
    ownership = WORKSTREAM_OWNERSHIP[stream["name"]]
    module_name = stream["modules"][index % len(stream["modules"])]
    segment = CUSTOMER_SEGMENTS[index % len(CUSTOMER_SEGMENTS)]
    account = CUSTOMER_ACCOUNTS[index % len(CUSTOMER_ACCOUNTS)]
    channel = SUPPORT_CHANNELS[index % len(SUPPORT_CHANNELS)]
    region = REGIONS[index % len(REGIONS)]
    capability = CAPABILITY_AREAS[story_index % len(CAPABILITY_AREAS)]
    signal = FAILURE_SIGNALS[index % len(FAILURE_SIGNALS)]
    root_cause = ROOT_CAUSES[(index * 2) % len(ROOT_CAUSES)]
    remediation = REMEDIATIONS[(index * 3) % len(REMEDIATIONS)]
    prevention = PREVENTION_ACTIONS[(index * 5) % len(PREVENTION_ACTIONS)]
    detection = DETECTION_SOURCES[(index * 7) % len(DETECTION_SOURCES)]
    scenario_family = SCENARIO_FAMILIES[(story_index + index) % len(SCENARIO_FAMILIES)]
    is_private = index % 11 == 0
    is_reopened_case = issue_class in {"Bug", "Incident"} and (index % 13 == 0)
    is_stalled_case = issue_class in {"Feature", "Support"} and (index % 37 == 0)
    is_misprioritized_case = issue_class in {"Support", "Incident"} and (index % 29 == 0)
    should_priority_change = issue_class in {"Bug", "Support", "Incident"} and (index % 6 == 0)
    has_incomplete_description = issue_class in {"Support", "Bug"} and (index % 17 == 0)
    has_missing_workflow_stage = issue_class in {"Support", "Bug"} and (index % 26 == 0)
    has_noisy_language = index % 17 == 0
    has_legacy_artifact = index % 19 == 0
    has_inconsistent_priority_signal = issue_class in {"Support", "Incident"} and (index % 28 == 0)
    risk_flag = "None"
    if is_reopened_case:
        risk_flag = "Reopened"
        status_id = 4
    elif is_stalled_case:
        risk_flag = "Stalled"
        if status_id in {3, 4, 5}:
            status_id = 2
    elif is_misprioritized_case:
        risk_flag = "Mis-prioritized"
        priority_id = 1

    initial_priority_id = priority_id
    if is_misprioritized_case:
        initial_priority_id = max(base_priority_id, 3)
    elif should_priority_change and priority_id > 1:
        initial_priority_id = priority_id - 1
    if has_inconsistent_priority_signal and priority_id > 1:
        priority_id = 1

    if issue_class == "Support":
        author_id = _pick(SUPPORT_AGENT_POOL, index)
        initial_assignee_id = _pick([4, 12, 2, 10], index)
        assigned_to_id = _pick([4, 12, 2, 10], index, offset=1)
    elif issue_class == "Incident":
        author_id = _pick([2, 7, 19], index)
        initial_assignee_id = _pick(INCIDENT_COMMAND_POOL, index)
        assigned_to_id = _pick(INCIDENT_COMMAND_POOL, index, offset=1)
    else:
        author_id = _pick(ownership["author_pool"], index)
        initial_assignee_id = _pick(ownership["assignee_pool"], index)
        assigned_to_id = _pick(ownership["assignee_pool"], index, offset=1)

    if is_private:
        assigned_to_id = _pick(SECURITY_REVIEWERS, index)
        initial_assignee_id = assigned_to_id

    done_ratio = {
        1: 5 + ((index * 3) % 20),
        2: 30 + ((index * 7) % 40),
        3: 85 + (index % 10),
        4: 55 + ((index * 5) % 25),
        5: 100,
    }[status_id]
    if is_stalled_case:
        done_ratio = min(done_ratio, 35)

    estimated_hours = ESTIMATED_HOURS_BY_ISSUE_CLASS[issue_class] + float((index % 4) * 2)
    spent_hours = round(estimated_hours * (done_ratio / 100.0), 2)

    status_path = _status_progression_for_issue(status_id, is_reopened_case)
    base_journal_count = 3 + (index % 3)
    journal_count = max(base_journal_count, len(status_path) - 1)
    ratio_progress = _done_ratio_progression(done_ratio, journal_count)
    decision_slot = 2 if journal_count > 2 else journal_count - 1

    detail_buckets: list[list[dict[str, str]]] = [[] for _ in range(journal_count)]
    for transition_idx, (old_status, new_status) in enumerate(zip(status_path, status_path[1:])):
        detail_buckets[min(transition_idx, journal_count - 1)].append(
            {
                "property": "attr",
                "name": "status_id",
                "old_value": str(old_status),
                "new_value": str(new_status),
            }
        )
    if initial_assignee_id != assigned_to_id:
        detail_buckets[decision_slot].append(
            {
                "property": "attr",
                "name": "assigned_to_id",
                "old_value": str(initial_assignee_id),
                "new_value": str(assigned_to_id),
            }
        )
    if initial_priority_id != priority_id:
        detail_buckets[decision_slot].append(
            {
                "property": "attr",
                "name": "priority_id",
                "old_value": str(initial_priority_id),
                "new_value": str(priority_id),
            }
        )

    journals = []
    journal_pool = [assigned_to_id, author_id, *ownership["watcher_pool"], *SUPPORT_AGENT_POOL]
    for journal_idx in range(journal_count):
        previous_ratio = 0 if journal_idx == 0 else ratio_progress[journal_idx - 1]
        current_ratio = ratio_progress[journal_idx]
        details = [
            {
                "property": "attr",
                "name": "done_ratio",
                "old_value": str(previous_ratio),
                "new_value": str(current_ratio),
            },
            *detail_buckets[journal_idx],
        ]
        style = _journal_style_for_index(journal_idx, journal_count, status_id, is_reopened_case)
        note = _journal_note(
            style=style,
            issue_class=issue_class,
            capability=capability,
            signal=signal,
            account=account,
            segment=segment,
            channel=channel,
            region=region,
            root_cause=root_cause,
            remediation=remediation,
            prevention=prevention,
            detection=detection,
            scenario_family=scenario_family,
            module_name=module_name,
            assigned_to_id=assigned_to_id,
            risk_flag=risk_flag,
            journal_idx=journal_idx,
            index=index,
            is_reopened_case=is_reopened_case,
        )
        if is_misprioritized_case and journal_idx == decision_slot:
            note += " Priority remains below customer impact and requires explicit override evidence."
        if has_noisy_language and journal_idx in {0, 1}:
            note += (
                f" {NOISY_CZ_EN_SNIPPETS[(index + journal_idx) % len(NOISY_CZ_EN_SNIPPETS)]} "
                f"Slang marker: {DOMAIN_SLANG_SNIPPETS[(index + journal_idx) % len(DOMAIN_SLANG_SNIPPETS)]}."
            )
        if has_legacy_artifact and journal_idx == decision_slot:
            note += f" {LEGACY_ARTIFACT_SNIPPETS[index % len(LEGACY_ARTIFACT_SNIPPETS)]}"
        if has_incomplete_description and journal_idx == 0:
            note += " Detail gap acknowledged: popis je neúplný, evidence doplníme po exportu."

        private_note = bool(is_private and journal_idx == 0)
        if issue_class == "Incident" and journal_idx == decision_slot and index % 6 == 0:
            private_note = True

        journals.append(
            {
                "id": 40000 + (index * 10) + journal_idx,
                "user_id": _pick(journal_pool, index, offset=journal_idx),
                "notes": note,
                "private_notes": private_note,
                "created_on": f"2026-02-{updated_day}T{9 + journal_idx:02d}:20:00Z",
                "details": details,
            }
        )

    attachments = []
    if index % 4 == 0 or (issue_class in {"Bug", "Incident"} and index % 9 == 0):
        attachment_id = 60000 + index
        artifact_label = ["trace", "timeline", "checklist", "har", "sql-plan"][index % 5]
        attachment_filename = f"{artifact_label}-{issue_id}.txt"
        attachments.append(
            {
                "id": attachment_id,
                "filename": attachment_filename,
                "filesize": 1024 + (index * 17),
                "content_type": "text/plain",
                "description": f"{artifact_label.title()} evidence for issue {issue_id}",
                "content_url": (
                    "http://mock-redmine.local/attachments/"
                    f"{attachment_id}/{attachment_filename}"
                ),
                "downloads": index % 20,
                "author_id": author_id,
                "created_on": f"2026-02-{updated_day}T11:45:00Z",
                "digest": f"digest-{attachment_id}",
            }
        )

    relations = []
    epic_issue_id = issue_id - story_position
    if story_position == 1:
        relations.append(
            {
                "id": 70000 + (index * 3),
                "issue_id": epic_issue_id,
                "relation_type": "blocks",
                "delay": 1,
            }
        )
    elif story_position == 2:
        relations.append(
            {
                "id": 70000 + (index * 3),
                "issue_id": epic_issue_id + 1,
                "relation_type": "relates",
                "delay": None,
            }
        )
    elif story_position == 3:
        relations.append(
            {
                "id": 70000 + (index * 3),
                "issue_id": epic_issue_id + 2,
                "relation_type": "duplicates" if story_index % 2 == 0 else "relates",
                "delay": None,
            }
        )
    elif story_position == 4:
        relations.append(
            {
                "id": 70000 + (index * 3),
                "issue_id": epic_issue_id + 3,
                "relation_type": "blocks" if story_index % 3 == 0 else "duplicates",
                "delay": None,
            }
        )
    if story_index > 0 and story_position in {2, 4} and index % 7 == 0:
        relations.append(
            {
                "id": 70000 + (index * 3) + 1,
                "issue_id": issue_id - len(ISSUE_CLASS_CYCLE),
                "relation_type": "relates",
                "delay": None,
            }
        )

    watcher_user_ids = {
        author_id,
        assigned_to_id,
        _pick(ownership["watcher_pool"], index),
        _pick(ownership["watcher_pool"], index, offset=1),
        _pick([7, 19], index),
    }
    if issue_class in {"Support", "Incident"}:
        watcher_user_ids.update(INCIDENT_COMMAND_POOL)
    if is_private:
        watcher_user_ids.update(SECURITY_REVIEWERS)
    if issue_class == "Epic":
        watcher_user_ids.update([3, 17])

    impact = _pick(IMPACT_BY_ISSUE_CLASS[issue_class], index)
    if is_misprioritized_case:
        impact = "High"
    if has_inconsistent_priority_signal:
        impact = "High"

    subject = _subject_for_issue(
        issue_class=issue_class,
        capability=capability,
        signal=signal,
        account=account,
        segment=segment,
        issue_id=issue_id,
    )
    description = _description_for_issue(
        issue_class=issue_class,
        stream=stream,
        module_name=module_name,
        capability=capability,
        signal=signal,
        root_cause=root_cause,
        remediation=remediation,
        prevention=prevention,
        detection=detection,
        account=account,
        segment=segment,
        channel=channel,
        region=region,
        scenario_family=scenario_family,
        risk_flag=risk_flag,
    )
    noise_flags: list[str] = []
    if has_incomplete_description:
        description = (
            f"{issue_class} for account {account}. TODO: doplnit RCA, chybí část evidence "
            f"z issue #{issue_id}; waiting for customer logs."
        )
        noise_flags.append("Incomplete Description")
    if has_noisy_language:
        description += f" {NOISY_CZ_EN_SNIPPETS[index % len(NOISY_CZ_EN_SNIPPETS)]}"
        description += f" Team slang: {DOMAIN_SLANG_SNIPPETS[index % len(DOMAIN_SLANG_SNIPPETS)]}."
        noise_flags.append("Noisy Language")
    if has_legacy_artifact:
        description += f" {LEGACY_ARTIFACT_SNIPPETS[index % len(LEGACY_ARTIFACT_SNIPPETS)]}"
        noise_flags.append("Legacy Terminology")
    if has_inconsistent_priority_signal:
        description += (
            " Priority metadata looks inconsistent: queue priority is low while legacy severity "
            "label marks this as critical."
        )
        noise_flags.append("Inconsistent Priority Signal")
    if has_missing_workflow_stage:
        noise_flags.append("Missing Workflow Stage")

    custom_fields = [
        {"id": 901, "name": "Module", "value": module_name},
        {"id": 902, "name": "Customer Impact", "value": impact},
        {
            "id": 904,
            "name": "Workflow Stage",
            "value": WORKFLOW_STAGE_BY_ISSUE_CLASS[issue_class],
        },
        {"id": 905, "name": "Workstream", "value": stream["name"]},
        {"id": 906, "name": "Customer Segment", "value": segment},
        {"id": 907, "name": "Issue Class", "value": issue_class},
        {"id": 908, "name": "Scenario Family", "value": scenario_family},
        {"id": 909, "name": "Risk Flag", "value": risk_flag},
        {"id": 910, "name": "Customer Account", "value": account},
    ]
    if has_missing_workflow_stage:
        custom_fields = [field for field in custom_fields if field["name"] != "Workflow Stage"]
    if has_inconsistent_priority_signal:
        custom_fields.append({"id": 912, "name": "Legacy Severity", "value": "SEV1-Legacy"})
    custom_fields.append(
        {
            "id": 911,
            "name": "Data Quality Flag",
            "value": " | ".join(sorted(set(noise_flags))) if noise_flags else "Clean",
        }
    )

    child_ids: list[int] = []
    if issue_class == "Epic":
        for offset in range(1, len(ISSUE_CLASS_CYCLE)):
            if index + offset < BULK_ISSUE_COUNT:
                child_ids.append(issue_id + offset)

    return {
        "id": issue_id,
        "project_id": project_id,
        "tracker_id": tracker_id,
        "status_id": status_id,
        "priority_id": priority_id,
        "subject": subject,
        "description": description,
        "author_id": author_id,
        "assigned_to_id": assigned_to_id,
        "start_date": f"2026-01-{created_day}",
        "due_date": (
            f"2026-02-{_day_str(1, index + 2, 28)}"
            if is_stalled_case
            else f"2026-03-{due_day}"
        ),
        "done_ratio": done_ratio,
        "is_private": is_private,
        "estimated_hours": estimated_hours,
        "spent_hours": spent_hours,
        "created_on": f"2026-01-{created_day}T10:00:00Z",
        "updated_on": f"2026-02-{updated_day}T20:30:00Z",
        "closed_on": f"2026-02-{updated_day}T18:00:00Z" if status_id in {3, 5} else None,
        "custom_fields": custom_fields,
        "journals": journals,
        "attachments": attachments,
        "relations": relations,
        "watcher_user_ids": sorted(watcher_user_ids),
        "child_ids": child_ids,
    }


def _add_bulk_issues(count: int = BULK_ISSUE_COUNT) -> None:
    for index in range(count):
        issue_id = 1000 + index
        ISSUES.append(_bulk_issue(issue_id, index))


def _issue_custom_field(issue: dict, field_name: str, default: str = "") -> str:
    for field in issue.get("custom_fields", []):
        if field.get("name") == field_name:
            value = field.get("value")
            return str(value) if value is not None else default
    return default


def _add_bulk_time_entries() -> None:
    entry_id = 87000
    bulk_issues = [issue for issue in ISSUES if issue["id"] >= 1000]
    sla_response_targets_hours = {1: 24.0, 2: 4.0, 3: 1.0, 4: 0.25}
    base_iterations_by_class = {
        "Epic": 3,
        "Feature": 3,
        "Bug": 2,
        "Support": 2,
        "Incident": 4,
    }
    activities_by_class = {
        "Epic": [
            {"id": 9, "name": "Development"},
            {"id": 15, "name": "Coordination"},
            {"id": 10, "name": "QA"},
        ],
        "Feature": [
            {"id": 9, "name": "Development"},
            {"id": 10, "name": "QA"},
            {"id": 15, "name": "Coordination"},
        ],
        "Bug": [
            {"id": 11, "name": "Support"},
            {"id": 9, "name": "Development"},
            {"id": 10, "name": "QA"},
        ],
        "Support": [
            {"id": 11, "name": "Support"},
            {"id": 15, "name": "Coordination"},
            {"id": 10, "name": "QA"},
        ],
        "Incident": [
            {"id": 12, "name": "Incident Response"},
            {"id": 14, "name": "Escalation"},
            {"id": 11, "name": "Support"},
            {"id": 10, "name": "QA"},
        ],
    }

    for index, issue in enumerate(bulk_issues):
        issue_class = _issue_custom_field(issue, "Issue Class", "Support")
        risk_flag = _issue_custom_field(issue, "Risk Flag", "None")
        account = _issue_custom_field(issue, "Customer Account", "unknown account")
        scenario_family = _issue_custom_field(issue, "Scenario Family", "Operations")
        status_id = issue["status_id"]
        priority_id = issue["priority_id"]
        target_response_hours = sla_response_targets_hours.get(priority_id, 4.0)

        first_response_hours = {
            "Epic": 7.0 + (index % 3) * 2.5,
            "Feature": 3.5 + (index % 3) * 1.0,
            "Bug": 1.2 + (index % 4) * 0.6,
            "Support": 0.8 + (index % 4) * 0.5,
            "Incident": 0.2 + (index % 3) * 0.3,
        }.get(issue_class, 2.0)

        if risk_flag == "Stalled":
            first_response_hours += 4.0
        if index % 17 == 0:
            first_response_hours += target_response_hours * 1.8
        is_sla_breach = first_response_hours > target_response_hours

        response_day = _day_str(1, index + int(first_response_hours // 24), 28)
        response_hour = (9 + int(first_response_hours) + (index % 5)) % 24
        response_minute = int((first_response_hours % 1) * 60)
        is_night_incident = issue_class == "Incident" and index % 9 == 0
        if is_night_incident:
            response_hour = 1 + (index % 3)
            response_minute = 10

        contributor_pool = [issue["assigned_to_id"], issue["author_id"], 10, 4, 12, 15]
        first_response_comment = (
            f"First response handled for {account} after {first_response_hours:.1f}h "
            f"(SLA target {target_response_hours:.2f}h) in {scenario_family} scenario."
        )
        if is_sla_breach:
            first_response_comment += " SLA breach simulation: delayed acknowledgement triggered escalation policy."
        if is_night_incident:
            first_response_comment += " night shift incident response logged during on-call window."

        first_response_entry_hours = round(0.3 + (index % 3) * 0.2, 1)
        TIME_ENTRIES.append(
            {
                "id": entry_id,
                "project_id": issue["project_id"],
                "issue_id": issue["id"],
                "user_id": contributor_pool[index % len(contributor_pool)],
                "activity": (
                    {"id": 12, "name": "Incident Response"}
                    if issue_class == "Incident"
                    else {"id": 11, "name": "Support"}
                ),
                "hours": first_response_entry_hours,
                "comments": first_response_comment,
                "spent_on": f"2026-02-{response_day}",
                "created_on": f"2026-02-{response_day}T{response_hour:02d}:{response_minute:02d}:00Z",
                "updated_on": f"2026-02-{response_day}T{response_hour:02d}:{response_minute:02d}:00Z",
            }
        )
        entry_id += 1

        iterations = base_iterations_by_class.get(issue_class, 2)
        if status_id == 1:
            iterations = 1
        elif status_id in {3, 5}:
            iterations += 1
        if risk_flag == "Stalled":
            iterations += 2

        escalation_spike = (
            issue_class == "Incident"
            and ((issue["id"] - 1000) // len(ISSUE_CLASS_CYCLE)) % 5 == 0
        )
        if escalation_spike:
            iterations += 2

        issue_total_hours = first_response_entry_hours
        activity_cycle = activities_by_class.get(issue_class, activities_by_class["Support"])
        for offset in range(iterations):
            day = _day_str(2, index + offset, 28)
            activity = activity_cycle[offset % len(activity_cycle)]
            base_hours = {
                "Epic": 2.0 + (offset % 3) * 1.0,
                "Feature": 1.6 + (offset % 3) * 0.7,
                "Bug": 1.1 + (offset % 2) * 0.8,
                "Support": 0.8 + (offset % 2) * 0.6,
                "Incident": 1.8 + (offset % 3) * 1.3,
            }.get(issue_class, 1.2)

            if status_id == 1:
                base_hours = min(base_hours, 0.8)
            if risk_flag == "Stalled" and offset >= iterations - 2:
                base_hours = 0.6
            if escalation_spike and offset >= iterations - 2:
                base_hours = 5.5 + (offset % 2) * 1.5

            comment = (
                f"{activity['name']} effort on {issue_class.lower()} workflow for {account}: "
                "evidence update and owner coordination."
            )
            if risk_flag == "Stalled" and offset >= iterations - 2:
                comment += " Work paused awaiting vendor evidence package."
            if escalation_spike and offset >= iterations - 2:
                comment += " escalation spike war-room: parallel responders synchronized mitigation."
            if status_id in {3, 5} and offset == iterations - 1:
                comment += " Resolution validation completed and KPI counters updated."

            created_hour = 10 + ((offset + index) % 8)
            if is_night_incident and offset == 0:
                created_hour = 23

            hours = round(base_hours, 1)
            issue_total_hours += hours
            TIME_ENTRIES.append(
                {
                    "id": entry_id,
                    "project_id": issue["project_id"],
                    "issue_id": issue["id"],
                    "user_id": contributor_pool[(index + offset + 1) % len(contributor_pool)],
                    "activity": activity,
                    "hours": hours,
                    "comments": comment,
                    "spent_on": f"2026-02-{day}",
                    "created_on": f"2026-02-{day}T{created_hour:02d}:15:00Z",
                    "updated_on": f"2026-02-{day}T{created_hour:02d}:15:00Z",
                }
            )
            entry_id += 1

        issue["spent_hours"] = round(max(issue_total_hours, 0.5), 1)


def _add_bulk_wiki_pages() -> None:
    bulk_issues = [issue for issue in ISSUES if issue["id"] >= 1000]
    article_catalog = [
        {
            "title": "SLA-Metrics-Guide",
            "focus": "response targets, breach detection, and escalation timing",
            "parent": "Incident-Triage-Playbook",
        },
        {
            "title": "Evidence-Timeline-FAQ",
            "focus": "timeline integrity and evidence ordering from journals and files",
            "parent": "Reporting-Citations",
        },
        {
            "title": "Root-Cause-Catalog",
            "focus": "root-cause families and validated remediation patterns",
            "parent": "Incident-Triage-Playbook",
        },
        {
            "title": "Escalation-Policy",
            "focus": "handoff ownership and incident command escalation guardrails",
            "parent": "Incident-Triage-Playbook",
        },
        {
            "title": "Citation-Quality-Checklist",
            "focus": "grounded citation rules across issue, wiki, and file evidence",
            "parent": "Reporting-Citations",
        },
    ]

    for index in range(BULK_WIKI_PAGE_COUNT):
        day = _day_str(1, index, 18)
        article = article_catalog[index % len(article_catalog)]
        primary_issue = bulk_issues[(index * 11 + 3) % len(bulk_issues)]
        related_issue = bulk_issues[(index * 11 + 7) % len(bulk_issues)]
        module = _issue_custom_field(primary_issue, "Module", "Unknown Module")
        issue_class = _issue_custom_field(primary_issue, "Issue Class", "Support")
        scenario_family = _issue_custom_field(primary_issue, "Scenario Family", "Operations")
        risk_flag = _issue_custom_field(primary_issue, "Risk Flag", "None")
        account = _issue_custom_field(primary_issue, "Customer Account", "unknown account")
        revision = 2 + ((index + primary_issue["id"]) % 4)
        title = f"{article['title']}-{index + 1}"
        linked_document_id = 92100 + (index % 18)
        wiki_text = (
            f"Revision {revision} of {article['title']} covers {article['focus']}. "
            f"Primary evidence from issue #{primary_issue['id']} ({issue_class}, module {module}) "
            f"and corroborating thread issue #{related_issue['id']}. "
            f"Scenario family: {scenario_family}; risk flag: {risk_flag}; account: {account}. "
            f"Use document #{linked_document_id} and attached issue files as citation anchors."
        )
        wiki_comment = (
            f"Revision {revision}: integrated findings from issues "
            f"#{primary_issue['id']} and #{related_issue['id']}."
        )
        if index % 6 == 0:
            wiki_text += f" {NOISY_CZ_EN_SNIPPETS[index % len(NOISY_CZ_EN_SNIPPETS)]}"
            wiki_comment += " Mixed CZ/EN phrasing kept intentionally for historical realism."
        if index % 7 == 0:
            wiki_text += f" {LEGACY_ARTIFACT_SNIPPETS[index % len(LEGACY_ARTIFACT_SNIPPETS)]}"
            wiki_comment += " Legacy term left for audit compatibility."
        WIKI_PAGES.append(
            {
                "project_id": 1,
                "project_identifier": "platform-core",
                "title": title,
                "text": wiki_text,
                "version": revision,
                "author_id": [14, 20, 3, 8, 17][index % 5],
                "comments": wiki_comment,
                "updated_on": f"2026-02-{day}T12:00:00Z",
                "parent": article["parent"],
            }
        )


def _add_bulk_news_documents_files() -> None:
    bulk_issues = [issue for issue in ISSUES if issue["id"] >= 1000]
    wiki_topics = [
        "SLA-Metrics-Guide",
        "Evidence-Timeline-FAQ",
        "Root-Cause-Catalog",
        "Escalation-Policy",
        "Citation-Quality-Checklist",
    ]

    for index in range(BULK_NEWS_COUNT):
        day = _day_str(1, index, 28)
        primary_issue = bulk_issues[(index * 13 + 5) % len(bulk_issues)]
        related_issue = bulk_issues[(index * 13 + 9) % len(bulk_issues)]
        module = _issue_custom_field(primary_issue, "Module", "Unknown Module")
        scenario_family = _issue_custom_field(primary_issue, "Scenario Family", "Operations")
        risk_flag = _issue_custom_field(primary_issue, "Risk Flag", "None")
        wiki_title = f"{wiki_topics[index % len(wiki_topics)]}-{(index % 20) + 1}"
        news_type = index % 3
        if news_type == 0:
            title = f"Release update {index + 1}: {module} stabilization"
            summary = (
                f"Release note for issues #{primary_issue['id']} and #{related_issue['id']}."
            )
            description = (
                f"Release update documents production rollout and rollback checks for issue "
                f"#{primary_issue['id']} with companion fix issue #{related_issue['id']}. "
                f"See wiki {wiki_title} and document #{92100 + (index % 18)}."
            )
        elif news_type == 1:
            title = f"Incident review {index + 1}: {scenario_family} follow-up"
            summary = (
                f"Incident review and customer impact follow-up for issue #{primary_issue['id']}."
            )
            description = (
                f"Incident review summarizes detection, ownership handoff, and corrective actions "
                f"for issue #{primary_issue['id']} (risk {risk_flag}). References wiki {wiki_title}."
            )
        else:
            title = f"Process change {index + 1}: support workflow calibration"
            summary = (
                f"Process change introduced from evidence in issue #{primary_issue['id']}."
            )
            description = (
                f"Process change updates triage and citation workflow based on issues "
                f"#{primary_issue['id']} and #{related_issue['id']} in module {module}. "
                f"Validation notes are linked from document #{92100 + (index % 18)}."
            )
        if index % 4 == 0:
            summary += " Mixed note: část vstupů přišla CZ/EN a obsahuje support slang."
        if index % 5 == 0:
            description += f" {LEGACY_ARTIFACT_SNIPPETS[index % len(LEGACY_ARTIFACT_SNIPPETS)]}"
        NEWS.append(
            {
                "id": 91100 + index,
                "project_id": 1,
                "title": title,
                "summary": summary,
                "description": description,
                "author_id": [17, 15, 3, 14, 2][index % 5],
                "created_on": f"2026-02-{day}T08:00:00Z",
            }
        )

    for index in range(BULK_DOCUMENT_COUNT):
        day = _day_str(1, index, 28)
        primary_issue = bulk_issues[(index * 7 + 2) % len(bulk_issues)]
        related_issue = bulk_issues[(index * 7 + 5) % len(bulk_issues)]
        module = _issue_custom_field(primary_issue, "Module", "Unknown Module")
        issue_class = _issue_custom_field(primary_issue, "Issue Class", "Support")
        scenario_family = _issue_custom_field(primary_issue, "Scenario Family", "Operations")
        wiki_title = f"{wiki_topics[index % len(wiki_topics)]}-{(index % 20) + 1}"
        document_kind = [
            "Release readiness packet",
            "Incident review brief",
            "Process change proposal",
            "Knowledge remediation plan",
        ][index % 4]
        doc_description = (
            f"{document_kind} consolidates issue #{primary_issue['id']} ({issue_class}) "
            f"and related issue #{related_issue['id']} for scenario {scenario_family}. "
            f"Cross-reference wiki {wiki_title} and file bundle starting with "
            f"supporthub-{module.lower().replace(' ', '-')}-issue-{primary_issue['id']}."
        )
        if index % 6 == 0:
            doc_description += f" {NOISY_CZ_EN_SNIPPETS[index % len(NOISY_CZ_EN_SNIPPETS)]}"
        if index % 8 == 0:
            doc_description += f" {LEGACY_ARTIFACT_SNIPPETS[index % len(LEGACY_ARTIFACT_SNIPPETS)]}"
        DOCUMENTS.append(
            {
                "id": 92100 + index,
                "project_id": 1,
                "category_id": (index % 4) + 1,
                "title": f"{document_kind} {index + 1}: {module}",
                "description": doc_description,
                "created_on": f"2026-02-{day}T10:00:00Z",
            }
        )

    file_artifacts = [
        ("diagnostic-log", "log", "text/plain"),
        ("rollback-checklist", "md", "text/markdown"),
        ("evidence-export", "csv", "text/csv"),
        ("timeline-snapshot", "json", "application/json"),
        ("postmortem-notes", "txt", "text/plain"),
        ("query-plan", "sql", "text/plain"),
    ]

    for index in range(BULK_FILE_COUNT):
        day = _day_str(1, index, 28)
        file_id = 93100 + index
        primary_issue = bulk_issues[(index * 9 + 4) % len(bulk_issues)]
        related_issue = bulk_issues[(index * 9 + 8) % len(bulk_issues)]
        module = _issue_custom_field(primary_issue, "Module", "Unknown Module")
        scenario_family = _issue_custom_field(primary_issue, "Scenario Family", "Operations")
        artifact_prefix, ext, content_type = file_artifacts[index % len(file_artifacts)]
        filename = (
            f"supporthub-{artifact_prefix}-issue-{primary_issue['id']}-{index + 1}.{ext}"
        )
        wiki_title = f"{wiki_topics[index % len(wiki_topics)]}-{(index % 20) + 1}"
        file_description = (
            f"Evidence artifact for issue #{primary_issue['id']} with related case "
            f"#{related_issue['id']} ({scenario_family}, module {module}). "
            f"Referenced by wiki {wiki_title} and document #{92100 + (index % 18)}."
        )
        if index % 7 == 0:
            file_description += " Historical note: artifact label follows deprecated naming scheme v1."
        if index % 9 == 0:
            file_description += f" {NOISY_CZ_EN_SNIPPETS[index % len(NOISY_CZ_EN_SNIPPETS)]}"
        FILES.append(
            {
                "id": file_id,
                "project_id": 1,
                "filename": filename,
                "filesize": 1200 + (index * 37),
                "content_type": content_type,
                "description": file_description,
                "content_url": (
                    "http://mock-redmine.local/files/"
                    f"{file_id}/{filename}"
                ),
                "author_id": primary_issue["assigned_to_id"],
                "created_on": f"2026-02-{day}T14:00:00Z",
            }
        )


def _add_bulk_boards_and_messages() -> None:
    bulk_issues = [issue for issue in ISSUES if issue["id"] >= 1000]
    message_authors = [2, 3, 8, 10, 15, 17, 19]

    BOARDS.append(
        {
            "id": 94003,
            "project_id": 1,
            "name": "Operations Cadence",
            "description": (
                "Weekly operational coordination threads linking incidents, architecture choices, "
                "and follow-up actions."
            ),
            "position": 2,
            "is_private": False,
            "topics_count": BULK_OPS_TOPIC_COUNT,
            "messages_count": BULK_OPS_TOPIC_COUNT * 2,
        }
    )

    message_id = 96000
    for index in range(BULK_OPS_TOPIC_COUNT):
        topic_id = message_id
        day = _day_str(1, index, 28)
        primary_issue = bulk_issues[(index * 15 + 3) % len(bulk_issues)]
        related_issue = bulk_issues[(index * 15 + 8) % len(bulk_issues)]
        module = _issue_custom_field(primary_issue, "Module", "Unknown Module")
        issue_class = _issue_custom_field(primary_issue, "Issue Class", "Support")
        risk_flag = _issue_custom_field(primary_issue, "Risk Flag", "None")
        scenario_family = _issue_custom_field(primary_issue, "Scenario Family", "Operations")
        is_architecture_thread = index % 3 == 0
        if is_architecture_thread:
            subject = (
                f"Architecture review week {index + 1}: {module} tradeoff "
                f"(issue #{primary_issue['id']})"
            )
            topic_content = (
                f"Architecture thread for module {module}: compare mitigation options from issue "
                f"#{primary_issue['id']} and dependency issue #{related_issue['id']}. "
                f"Decision point: choose strategy documented in document #{92100 + (index % 18)} "
                f"and align with wiki Evidence-Timeline-FAQ-{(index % 20) + 1}."
            )
        else:
            subject = (
                f"Ops review week {index + 1}: {scenario_family} follow-up "
                f"(issue #{primary_issue['id']})"
            )
            topic_content = (
                f"Operational review for issue #{primary_issue['id']} ({issue_class}, risk {risk_flag}) "
                f"with related case #{related_issue['id']}. "
                f"Decision point: confirm escalation owner and link action log to document "
                f"#{92100 + (index % 18)}."
            )
        if index % 4 == 0:
            topic_content += f" {NOISY_CZ_EN_SNIPPETS[index % len(NOISY_CZ_EN_SNIPPETS)]}"
        if index % 5 == 0:
            topic_content += f" {LEGACY_ARTIFACT_SNIPPETS[index % len(LEGACY_ARTIFACT_SNIPPETS)]}"

        reply_content = (
            f"Follow-up confirmed: owner assigned, issue #{primary_issue['id']} timeline updated, "
            f"and file supporthub-evidence-export-issue-{primary_issue['id']}-{index + 1}.csv "
            f"attached to communication packet. Next checkpoint references wiki "
            f"Citation-Quality-Checklist-{(index % 20) + 1}."
        )
        if index % 3 == 0:
            reply_content += (
                " FYI z provozu: handoff byl trochu ping-pong, ale rozhodnutí je zdokumentované."
            )

        MESSAGES.append(
            {
                "id": topic_id,
                "board_id": 94003,
                "project_id": 1,
                "parent_id": None,
                "author_id": message_authors[index % len(message_authors)],
                "subject": subject,
                "content": topic_content,
                "replies_count": 1,
                "last_reply_id": topic_id + 1,
                "locked": False,
                "sticky": 0,
                "created_on": f"2026-02-{day}T09:00:00Z",
                "updated_on": f"2026-02-{day}T09:30:00Z",
            }
        )
        MESSAGES.append(
            {
                "id": topic_id + 1,
                "board_id": 94003,
                "project_id": 1,
                "parent_id": topic_id,
                "author_id": message_authors[(index + 1) % len(message_authors)],
                "subject": f"Re: {subject}",
                "content": reply_content,
                "replies_count": 0,
                "last_reply_id": None,
                "locked": False,
                "sticky": 0,
                "created_on": f"2026-02-{day}T09:30:00Z",
                "updated_on": f"2026-02-{day}T09:30:00Z",
            }
        )
        message_id += 2


def _generate_bulk_data() -> None:
    _add_bulk_issues(count=BULK_ISSUE_COUNT)
    _add_bulk_time_entries()
    _add_bulk_wiki_pages()
    _add_bulk_news_documents_files()
    _add_bulk_boards_and_messages()

    if len(ISSUES) < 100:
        raise RuntimeError("Fixture generation failed: expected at least 100 issues")


_generate_bulk_data()
