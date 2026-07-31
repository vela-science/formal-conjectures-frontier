# Kernel-verified Lean theorems

The current Vela repository for exact formal statements, sorry-free Lean
proofs, and source-bound evidence from
[`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures).
When a current Target Index exists, it selects one bounded task. Lean tasks use
a separate frozen capsule that owns the statement, checks the candidate with
the kernel, and audits `#print axioms` for `sorryAx`. Cross-Frontier reference
tasks retain exact attributed evidence without importing source Standing.

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
- Current and closed Target packets: [`targets/`](targets/)
- Signed predecessor: `pre-current-epoch/1e40ffada7ef`

```bash
vela status . --json
vela next . --limit 1 --json
vela check . --strict --json
```

There is currently no offered Target. Do not revive completed work from a
packet left outside the index. The completed Erdős 505 task remains exactly
recoverable at tag `pre-compaction/84d3064cd7d9`: Submission
`vsb_c50dc7e85cb76684` (`sha256:9adecb4649fa99a7b0945e99f3197cb72489e17b4bd08fe2bfcdff7d0f1c67d3`)
and Verification `vvr_a898f5218acb57e9`
(`sha256:70a2f95366d1f9e55fa46c84d3ffa61f54d957427cdf0bf282017a5d26b324a4`).

When `vela next` exposes a new exact Target, start it before submitting:

```bash
vela submit --frontier . --attempt <vat_id> \
  --claim "<bounded result>" --type computational \
  --replayability exact --artifact <path>:<kind> \
  --caveat "<scope and authority limits>" --as agent:<you> --json
```

Each accepted Claim records the fully qualified declaration and its exact
axiom set. A clean kernel check does not establish statement fidelity or
mathematical significance; those remain explicit review questions.
