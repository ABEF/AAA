# Maintaining the project Todo

## Callable function reference maintenance

When a public/external function, parameter, output, permission or behavior changes,
update [the source-bound function reference](CONTRACT_FUNCTIONS.md) and its concise
behavior/authority notes with the same change. Regenerate from the current normal
compiler ABI and check source bindings; do not hand-edit signatures or infer
permissions from visibility alone. The operator manual links this reference at
its end, while retaining exact procedures and failure/recovery boundaries.

**[TODO.md](../TODO.md) is the only task-status checklist.** It is ordered with Smart contracts first, Backend second and Frontend third, followed by Creator tasks / ZZZ team, testing, security/audit, operations and future migration. Expand a task's acceptance criteria for its detailed release requirements. The website has no Todo page or generated task data.

| Document | Purpose | Update when |
| --- | --- | --- |
| [Project Todo](../TODO.md), generated from [the ledger](project-todo.json) | Tasks, status, remaining work and acceptance criteria | Work progresses or a requirement changes |
| [Feature and evidence reference](IMPLEMENTATION_STATUS.md) | What the candidate implements, its boundaries and source-bound verification | Behavior or evidence changes |
| [Release approval record](RELEASE_CHECKLIST.md) | Exact candidate, configuration, reviewer decisions and final go/no-go | A release is submitted for review or approved/rejected |
| [Operator manual](OPERATOR_MANUAL.md) | Management actions, roles, parameters, incidents and recovery procedures | Any operator-facing functionality, command, permission, limit or behavior changes |
| [Engineering roadmap](ROADMAP.md) | Work sequence and dependencies, linked to the owning Todo tasks | Sequencing, prerequisites or pre-seal boundaries change |

The [security audit plan](SECURITY_AUDIT_PLAN.md) explains threat models and review criteria. It does not carry a separate task status. The old implementation/release filenames remain stable for existing links; neither is another Todo.

Questions requiring the token/pool creator belong in [Creator tasks / ZZZ team](../TODO.md#creator-tasks--zzz-team). Record the dated answer, responsible party and evidence there; keep implementation and independent qualification in the linked technical task. An answer does not close its technical release gate. Preserve stable IDs when moving a task between sections.

For every feature, fix, resolved issue, new task or decision:

1. Update [project-todo.json](project-todo.json): status, remaining work, optional `acceptance` criteria and review date. Use stable unique task IDs; each generates a `TODO.md#task-<id>` link. Give every task an `href` to its most relevant published repository file or section, relative to the repository root; its title stays clickable. Keep links current when files move. Record task status only here. Update the feature reference only when behavior/evidence changes, and the approval record only when release scope or a review decision changes. Do not copy unchecked task lists into either reference.
2. Review operator impact. Update [the operator manual](OPERATOR_MANUAL.md) and linked specialist runbooks in the same change for new/changed functions, permissions, defaults, configuration, lifecycle, service behavior and failure modes. Include the exact call/config, authority, prerequisites, effects, verification, stop/restart, rollback and irreversible boundaries. If no procedure changes, explicitly record that conclusion in the change summary. Check source/ABI names and document links; reuse unchanged test evidence. The manual describes procedures, never a second task-status list.
3. Run `python scripts/sync-project-todo.py`, then the same command with `--check`. Generated `TODO.md` must match the ledger. Reconcile roadmap prerequisites and task links when the work sequence changes; it must not maintain a second status list. A local implementation, provider choice, production rehearsal and audit are different milestones.
4. Commit and push the intended checklist changes to ABEF/AAA. Do not include unrelated working changes just to publish a task update. Verify the remote commit/file before reporting it published.
5. Update repository context when decisions change. Website product changes still follow local verification, website commit/push and server deployment; Todo-only changes do not modify or redeploy the website.
6. Report local and GitHub status separately. If publishing is blocked, state the outstanding step. Do not promise synchronization based on local saves.

This is a required development procedure, not a background synchronization service. Future sessions must read the repository instructions. No global personal memory is assumed.
