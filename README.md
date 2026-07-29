# Kernel-verified Lean theorems

The current Vela repository for exact formal statements, sorry-free Lean
proofs, and source-bound evidence from
[`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures).
A content-addressed Target Index selects one bounded task. Lean tasks use a
separate frozen capsule that owns the statement, checks the candidate with the
kernel, and audits `#print axioms` for `sorryAx`. Cross-Frontier reference
tasks retain exact attributed evidence without importing source Standing.
Canopus remains removable producer scaffolding.

Verifier success is evidence, not acceptance. A producer Submission, an
independent Verification Record, and a repository-authority Decision are
distinct signed objects.

This repository is the maintained successor to the historical
`formal-conjectures-lean` and `prover-lane` frontiers. Their audit history is
preserved, but they are not active product surfaces.

## Repository contract

- Epoch: [`.vela/epoch.json`](.vela/epoch.json)
- Current object index: [`.vela/repository.json`](.vela/repository.json)
- Repository authority: [`.vela/authority/`](.vela/authority/)
- Scientific records: [`records/`](records/)
- Target packet: [`targets/`](targets/)
- Signed predecessor: `pre-current-epoch/1e40ffada7ef`

```bash
vela status . --json
vela next . --limit 1 --json
vela start formal:retain-erdos-424-correction \
  --frontier . --as agent:<you> --json
vela check . --strict --json
```

After producing and checking the exact target:

```bash
vela submit --frontier . --attempt <vat_id> \
  --claim "<bounded result>" --type computational \
  --replayability exact --artifact <path>:<kind> \
  --caveat "<scope and authority limits>" --as agent:<you> --json
```

Each accepted Claim records the fully qualified declaration and its exact
axiom set. A clean kernel check does not establish statement fidelity or
mathematical significance; those remain explicit review questions.
