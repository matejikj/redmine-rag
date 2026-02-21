# SupportHub Personas and Ownership (Data Task 2)

## 1. Scope

This blueprint defines realistic users, role responsibilities, group topology, and issue assignment rules for the SupportHub project.

## 2. Persona Set

Target size:
- 20 users (within required 15-30 range).

Primary roles represented:
- Support Agent (L1/L2)
- Tech Lead
- Product Owner
- Customer Success
- Security Engineer
- Incident Manager
- Incident Commander
- SRE
- Data Analyst
- Backend Engineer
- Knowledge Manager
- Integrations Engineer
- Release Manager
- Security Analyst
- Technical Writer

Behavior principles:
- Product Owner initiates scope-driven workstreams.
- Tech and security roles own sensitive/critical remediation.
- Support roles handle intake and customer-facing updates.
- Customer Success appears in watcher/handoff paths for high-impact issues.

## 3. Group Topology

Groups in fixtures map to real operational boundaries:
- `SupportHub Incident Command`
- `SupportHub Identity Squad`
- `SupportHub SLA Automation`
- `SupportHub Timeline & Data`
- `SupportHub Knowledge Guild`
- `SupportHub Agent Pool`
- `SupportHub Product Council`

Each group has user membership aligned to competencies, not random assignment.

## 4. Workstream Ownership Map

Authentication:
- Authors: Product/Tech (`PO`, `Tech Lead`, `Backend Engineer`)
- Assignees: Identity implementers + security
- Watchers: Incident manager, customer success, release, security analyst

SLA Automation:
- Authors: Product + incident operations
- Assignees: Incident manager, SRE, incident commander
- Watchers: Customer success + release stakeholders

Evidence Timeline:
- Authors: Data/integrations/product
- Assignees: Backend, integrations, SRE
- Watchers: Incident + CS + release

Knowledge Base:
- Authors: Knowledge manager / technical writer / product
- Assignees: Knowledge owner + support L2
- Watchers: Customer success + support team

Reporting & Citations:
- Authors: Data + product + knowledge
- Assignees: Data/integrations/release
- Watchers: Incident + CS + documentation

## 5. Assignment Rules

Deterministic rules implemented in fixture generation:
- Author and assignee are selected from workstream-specific ownership pools.
- Private issues are rerouted to security reviewers.
- Journal participants are derived from assignee + author + watcher pools.
- Watchers always include accountability roles (author, CS, area watchers).

These rules ensure role-based handoff traces in journals and watchers.

## 6. Data Quality Requirements

- At least 5 distinct role families appear in live issue flows.
- Private tickets must involve security roles in assignment and comments.
- Assignment distribution must be explainable by workstream ownership.
- No issue assignment uses random user IDs outside ownership model.

## 7. Acceptance Mapping

`data-task-2` acceptance coverage:
- 15-30 realistic users with role context: satisfied.
- Group/ownership map by areas: satisfied.
- Role-based assignment rules: satisfied.
