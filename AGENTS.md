# Formal Conjectures Frontier agent guide

This is the only canonical agent guide for this repository. The scientific
source of truth is Git plus the current Vela repository manifest; generated
vendor-specific instruction copies are intentionally not used.

## Agent rules

Agents may:

- inspect status, the current offer, exact records, and provenance
- inspect the first offered Target with the write-free `vela start` briefing
- use the frozen packet and its exact source, environment, and authority limits
- run only the named verifier
- retain one signed, bounded Submission binding the exact packet and verifier
- execute one exact repository-authority Decision when the human authority has
  explicitly authorized that Decision or the named campaign in the active
  Codex task, provided the agent uses the standard authority provider, binds
  the current Decision Inbox entry root, records the human-facing reason, and
  replays the repository before continuing

Agents may not:

- invoke a repository-authority Decision without explicit human authorization,
  infer authorization from verifier success, bypass the standard authority
  provider, or expose repository-authority credentials
- treat a kernel pass, Git commit, Submission, or model answer as acceptance
- change the frozen statement, package, dependencies, or authority limits after
  starting
- hand-edit `.vela/authority/`, `.vela/repository.json`, or retained records
- publish an upstream contribution in a human's name

## Fast commands

```bash
vela status . --json
vela next . --limit 1 --json
vela start <target> --frontier . --json
vela submit --frontier . \
  --claim "<bounded result>" --type <type> \
  --replayability exact --artifact <path>:<kind> \
  --caveat "<scope and authority limits>" \
  --packet-root <packet_sha256> --profile-root <profile_sha256> \
  --verifier-capsule-root <capsule_sha256> \
  --result-contract-root <contract_sha256> \
  --as agent:<name> --json
vela verification import . <verification.json> --as verifier:<name> --json
vela review list . --json
vela show . <object_id> --json
vela why . <claim_id> --json
vela check . --json
```

Use only the first ranked Target unless the canonical ranking facts change.
No Target is currently offered. Completed packets outside the current Target
Index are historical evidence, not work invitations.
External Lean runs are limited to a named Lean mission and its frozen capsule.
Foreign references remain attributed evidence with local Standing effect
`none` unless a separate human Decision says otherwise.
