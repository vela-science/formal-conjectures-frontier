# Kernel-verified Lean theorems

The current Vela repository for sorry-free Lean proofs of exact statements from
[`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures).
A content-addressed Target Index selects one collision-checked theorem. Canopus
is removable producer scaffolding; a separate frozen Lean capsule owns the
statement, checks the candidate with the kernel, and audits `#print axioms` for
`sorryAx`.

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
vela start formal:erdos-505-test-dim-one \
  --frontier . --as agent:<you> --json
vela check . --strict --json
```

After producing and kernel-checking the exact target:

```bash
vela submit --frontier . --attempt <vat_id> \
  --claim "<exact theorem result>" --type theoretical \
  --replayability exact --artifact <path>:lean-proof \
  --caveat "<statement-fidelity limits>" --as agent:<you> --json
```

Each accepted Claim records the fully qualified declaration and its exact
axiom set. A clean kernel check does not establish statement fidelity or
mathematical significance; those remain explicit review questions.
