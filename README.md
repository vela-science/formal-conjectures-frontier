# Kernel-verified Lean theorems

The current Vela repository for exact formal statements, sorry-free Lean
proofs, and source-bound evidence from
[`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures).
Open work is offered only when this Frontier has a real bounded task. Lean tasks use
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

- Current origin and compacted predecessor: [`.vela/origin.json`](.vela/origin.json)
- Current object index: [`.vela/repository.json`](.vela/repository.json)
- Repository authority: [`.vela/authority/`](.vela/authority/)
- Scientific records: [`records/`](records/)
- Current and closed Target packets: [`targets/`](targets/)
- Compacted predecessor: `pre-compaction/c2719d14aae9`

```bash
vela status . --json
vela check . --json
```

There is currently no offered Target, so this repository has no `targets.json`.
Do not revive completed work from a retained packet. The completed Erdős 505 task remains exactly
recoverable at tag `pre-compaction/84d3064cd7d9`: Submission
`vsb_c50dc7e85cb76684` (`sha256:9adecb4649fa99a7b0945e99f3197cb72489e17b4bd08fe2bfcdff7d0f1c67d3`)
and Verification `vvr_a898f5218acb57e9`
(`sha256:70a2f95366d1f9e55fa46c84d3ffa61f54d957427cdf0bf282017a5d26b324a4`).

When `vela next` exposes a new exact Target, start it before submitting:

```bash
vela start <target> --frontier . --json
vela submit --frontier . \
  --claim "<bounded result>" --type computational \
  --replayability exact --artifact <path>:<kind> \
  --caveat "<scope and authority limits>" \
  --packet-root <packet_sha256> --profile-root <profile_sha256> \
  --verifier-capsule-root <capsule_sha256> \
  --result-contract-root <contract_sha256> \
  --as agent:<you> --json
```

`vela start` is a write-free briefing. It creates no Attempt, lease, or
approval step and prints the exact roots required by the Submission.

Each accepted Claim records the fully qualified declaration and its exact
axiom set. A clean kernel check does not establish statement fidelity or
mathematical significance; those remain explicit review questions.
