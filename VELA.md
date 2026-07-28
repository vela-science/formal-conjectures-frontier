# Formal Conjectures frontier — agent charter

This is a current Vela repository for kernel-checked Lean proofs
(`vfr_97d7d25957384f80`). `.vela/epoch.json` binds the predecessor,
`.vela/repository.json` indexes current objects, `.vela/authority/` holds
repository authority, and `records/` holds content-addressed scientific
records.

The producer path is `status -> next -> start -> submit`. A Submission is
producer input. Verification and repository-authority decisions are separate
signed records.

`vela agents sync` regenerates tool-specific agent guidance from this file.

## Agent rules

Agents may:

- inspect status, the current offer, exact records, and provenance
- start the first offered Target with an explicit `agent:` identity
- use the frozen packet, Lean version, dependencies, and axioms policy
- run the named kernel verifier
- register one signed, bounded Submission from the active Attempt

Agents may not:

- invoke repository-authority decisions or use authority credentials
- treat a kernel pass, Git commit, Submission, or model answer as acceptance
- change the frozen statement, dependencies, or axioms policy after starting
- hand-edit `.vela/authority/`, `.vela/repository.json`, or retained records
- publish an upstream contribution in a human's name

## Fast commands

```bash
vela status . --json
vela next . --limit 1 --json
vela start <target> --frontier . --as agent:<name> --json
vela submit --frontier . --attempt <vat_id> \
  --claim "<exact theorem result>" --type theoretical \
  --replayability exact --artifact <path>:lean-proof \
  --caveat "<statement-fidelity limits>" --as agent:<name> --json
vela review list . --json
vela show . <object_id> --json
vela why . <claim_id> --json
vela check . --strict --json
```

Use only the first ranked Target unless the canonical ranking facts change.
External Lean runs are limited to that named mission and its frozen capsule.
