# Maintaining the project Todo

The user changed the requested location on 2026-10-16: **keep the central Todo in the contract repository on GitHub, not in the website frontend**. [TODO.md](../TODO.md) is ordered with Smart contracts first, Backend second and Frontend third, followed by testing, security/audit, operations and future migration. The [security audit plan](SECURITY_AUDIT_PLAN.md) supplies acceptance criteria, not a second task-status ledger. The website has no Todo page or generated task data.

For every feature, fix, resolved issue, new task or decision:

1. Update [project-todo.json](project-todo.json): status, remaining work and review date. Use stable unique task IDs. Give every task an `href` to its most relevant published repository file or section, relative to the repository root; the generated task title is clickable. Keep these links current when files move. Reconcile affected details in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). Those contain evidence and release gates rather than another independent summary.
2. Run `python scripts/sync-project-todo.py`, then the same command with `--check`. Generated `TODO.md` must match the ledger. A local implementation, provider choice, production rehearsal and audit are different milestones.
3. Commit and push the intended checklist changes to ABEF/AAA. Do not include unrelated working changes just to publish a task update. Verify the remote commit/file before reporting it published.
4. Update repository context when decisions change. Website product changes still follow local verification, website commit/push and server deployment; Todo-only changes do not modify or redeploy the website.
5. Report local and GitHub status separately. If publishing is blocked, state the outstanding step. Do not promise synchronization based on local saves.

This is a required development procedure, not a background synchronization service. Future sessions must read the repository instructions. No global personal memory is assumed.
