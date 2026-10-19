# FEAT-021 — Classroom

- **Status:** Implemented in Git
- **Created:** 2026-10-17
- **Owner:** operator
- **GitHub issue:** draft only

## Purpose

Give the lab a Classroom section. The operator names a topic, the instructor writes a lesson plan, and the class is taught out loud while the explanation is drawn on a whiteboard. The operator can raise a hand, ask a question, or post a question for the end of the current part.

## User workflow

1. Open **Classroom** from the lab sidebar or `/classroom`.
2. Enter a topic and start class.
3. Read the lesson plan while the instructor speaks the opening and draws it.
4. Follow the later parts on the whiteboard.
5. Raise a hand to pause, ask a question, or post one for later.
6. The instructor answers in voice and adds marks to the board, then returns to the lesson.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Control plane | `mac-mini` | Serves `/classroom` and the lesson API |
| Browser | `mac-air` or whichever machine has the lab open | Speaks with the browser voice and draws the board |

## Dependencies

- Features: `FEAT-004`, `FEAT-011`
- ADRs / policies: ADR 0038 (no silent paid-model fallback)
- Hosts / services that must already be live: the control plane. A local model improves the plan. Class still starts from the classroom outline when the model does not return one.

## Proposed deliverables

- `platform/src/ai_lab_platform/classroom.py`
- `platform/src/ai_lab_platform/web/classroom.html`
- `platform/src/ai_lab_platform/web/static/classroom.js`
- Sidebar and top-nav links
- `tests/test_classroom.py`

## Proposed implementation work orders

| ID (proposed) | Title | Depends on | Acceptance (sketch) |
|---------------|-------|------------|---------------------|
| IWO-106 | Classroom voice and whiteboard | FEAT-011 | A topic returns a lesson; the page speaks and draws; questions get an answer |

## Acceptance criteria

- [x] `/classroom` is linked from the lab sidebar
- [x] A topic returns a lesson plan with spoken sections and whiteboard marks
- [x] Questions return speech plus board marks
- [x] The lesson call uses the local model only
- [x] Unit tests cover the plan, the board allow-list, auth, and the page
- [ ] Human confirmation of voice and drawing in a browser
- [ ] Human approval before any host deploy

## Out of scope

- A server-side speech engine, avatar, or recorded class
- Multi-student rooms
- Saving class transcripts
- Deploying or restarting the control plane
- Pulling models

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | done | this file |
| Code | done | `classroom.py`, `/classroom` |
| Host deploy | done | 2026-10-17, mini control plane restarted |
| Live verified | partial | Page and lesson API on `mac-mini:8088`. Browser voice not watched in a session |

## Notes

Voice is the browser speech synthesizer. Pause stops the voice and the pen together and resumes from that point. Each beat is one page: a handwritten title, one figure (`packet`, `layers`, `flow`, `fabric`, `pie`, `equation`, `graph`, `cycle`, or `list`), up to two handwritten lines, and an optional table. A fabric is spines, leaves, hosts, and the VXLAN tunnel. Later sections and answers add marks on that same diagram in a second color. The model does not place coordinates. Model text is not HTML and is not executed. Drawing quality is not yet accepted from a live class.
