# AGENTS.md

## Roles
- Codex = logic, planning, review, doc updates
- Claude Code = implementation only
- User = approval gate between phases

## Workflow
1. Read docs/NEXT_STEPS.md first
2. Treat docs/NEXT_STEPS.md as the current task authority
3. Update docs/DEV_LOG.md after any coding task
4. Export artifacts/latest_patch.diff after any coding task
5. Do not start the next phase unless explicitly instructed

## Hard rules
- Do only the scoped task
- No refactors unless explicitly requested
- No prior-phase cleanup unless explicitly requested
- No invented logic or guardrails
- Prefer the smallest correct patch
- Keep output concise

## Required output format
1. STATUS
2. FILES CHANGED
3. BEHAVIORAL IMPACT
4. NOT TOUCHED
5. DEFERRED CLEANUP NOTES
6. ARTIFACTS UPDATED

## Compacting
If the thread is getting long or repetitive, remind the user to compact before the next phase.
