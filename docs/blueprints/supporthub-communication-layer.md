# SupportHub Communication Layer Blueprint (Data Task 7)

## Goal
Provide realistic board/message data that reflects actual team coordination across architecture, operations, and security work.

## Board Topology
- `Architecture Discussions` (public): technical tradeoffs and implementation decisions.
- `Operations Cadence` (public): weekly operational follow-up with action tracking.
- `Security Review Board` (private): restricted security and production incident threads.

## Thread Design
Each topic thread should include:
- explicit references to issues (`issue #...`)
- links to knowledge artifacts (`document #...`, wiki references, file package references)
- decision signals (`Decision:` or `Decision point:`)
- at least one follow-up reply for operational cadence topics

## Coverage Expectations
- Mix of architecture and operations threads in public boards.
- Security board contains private incident/security context.
- Content supports RAG retrieval for communication-based evidence.

## Visibility Rules
- Public boards/topics/messages are accessible with normal auth.
- Private security board is forbidden for non-admin and visible for admin.

## Acceptance Mapping
- Message linkage to issues/docs: enforced by explicit references in topic and reply content.
- Decision points visible in threads: enforced by decision markers.
- Private/public consistency: enforced by board visibility settings and API auth checks.
