---
name: metabase-hol-guard
description: Protect local AI coding-agent sessions with HOL Guard before state-changing Metabase CLI or repository workflows.
---

# Metabase + HOL Guard

Use HOL Guard as the local agent-runtime safety boundary before high-impact Metabase work. Keep Metabase authentication, permissions, review, backups, and verification authoritative. HOL Guard protects the supported local coding-agent harness; it does not replace Metabase access controls or claim to intercept server-side operations directly.

## Protect the local harness

Probe the actual HOL Guard CLI rather than relying on a platform-specific executable lookup:

```bash
hol-guard --version
```

If that command is unavailable and runtime protection was requested, prefer an isolated install:

```bash
pipx install hol-guard
```

Then initialize and detect the supported harness:

```bash
hol-guard bootstrap
hol-guard detect --json
```

If the detected harness is `hermes`, use its dedicated bootstrap path instead:

```bash
hol-guard hermes bootstrap
```

For other supported harnesses, use the generic installer:

```bash
hol-guard install <harness>
```

Then keep the existing dry-run, launch, status, and harness-specific verification checks:

```bash
hol-guard run <harness> --dry-run
hol-guard run <harness>
hol-guard status
hol-guard doctor <harness> --json
```

Use the exact harness identifier reported by `detect --json`. Run the Metabase workflow from the protected harness launched by `hol-guard run`. If the dry run, status, or harness doctor reports an error or cannot prove the protection state, stop mutation-bearing Metabase work rather than falling back to an unprotected agent.

## Require Guard before mutations

Use the protected harness before agent-driven Metabase work that can create, update, archive, import, export, sync, change settings, publish content, modify embedding code, or alter deployment state. Read-only inspection can stay read-only.

If Guard blocks or requests review, stop before the protected operation and inspect it:

```bash
hol-guard approvals
hol-guard approvals open
hol-guard receipts
```

Never bypass a Guard decision by rerunning the operation outside the protected harness.

## Preserve Metabase controls

- Prefer the official `mb` CLI or documented Metabase workflow over ad hoc API calls when an official path exists.
- Keep Metabase authentication, RBAC, audit, backups, tests, and application validation in place.
- Review generated changes before committing or publishing them.
- Verify the Metabase result after the protected operation completes.
- If HOL Guard setup cannot be verified, report that the protected workflow is not ready instead of silently continuing unguarded.

Canonical HOL Guard setup and troubleshooting: https://github.com/hashgraph-online/hol-guard-plugin/tree/main/skills/hol-guard
