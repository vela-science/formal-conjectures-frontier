# Kernel-verified Lean theorems

The Vela frontier for sorry-free Lean proofs of exact statements from
`google-deepmind/formal-conjectures`. A derived, content-addressed target index
selects one collision-checked theorem. Canopus is a removable producer: it may
request a proof, but a separate frozen Lean capsule owns the statement, checks
the candidate with the kernel, and audits `#print axioms` for `sorryAx`.

Verifier success is evidence, not acceptance. `vela land` records a Receipt and
routes it under the signed policy; with no matching policy, the proposal stays
at Defer for an exact human decision. Neither Canopus nor a model sees a human
key or enters the trust path.

This frontier is the maintained successor to the historical
`formal-conjectures-lean` and `prover-lane` frontiers. Their audit history is
preserved, but they are not active product surfaces.

- State entrypoint: `frontier.json`
- Manifest: `frontier.yaml`
- Lockfile: `vela.lock`

```bash
vela status . --json
vela next . --limit 1 --json
vela work <target> --frontier . --as agent:<you> --json
vela check . --strict --json
vela reproduce .
```

Each finding records the fully-qualified decl, its axiom set (`{propext,
Classical.choice, Quot.sound}`, no `sorryAx`), and — where minted — a
content-addressed `vlv_` kernel-verification witness. Findings re-homed from
prover-lane whose proofs are still pending upstream PRs carry that note in their
caveats; a fresh `vlv_` gets attached once the proof merges into
google-deepmind/formal-conjectures.
