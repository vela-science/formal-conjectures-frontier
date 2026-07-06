# Kernel-verified Lean theorems (prover-in-the-loop)

The single Vela frontier for kernel-verified Lean theorems closed by the
**prover-in-the-loop foundry**. Known proved lemmas compose into proofs of open
theorems: `vela foundry lean-targets` selects a target, a Claude proof-subagent
produces a candidate proof, the **Lean kernel** verifies it (`vela foundry
lean-run`, `#print axioms` fail-closed on `sorryAx`), and a human signs the
result into state under the maintainer key. No model is in the trust path — the
kernel is the verifier, the human key is the accept.

This frontier consolidates the two former Lean frontiers (the earlier
`formal-conjectures-lean` and `prover-lane`); prover-lane is deprecated and its
routes redirect here.

- State entrypoint: `frontier.json`
- Manifest: `frontier.yaml`
- Lockfile: `vela.lock`

```bash
vela check . --strict --json
vela integrity . --json
vela reproduce .            # re-verify witnesses from scratch
```

Each finding records the fully-qualified decl, its axiom set (`{propext,
Classical.choice, Quot.sound}`, no `sorryAx`), and — where minted — a
content-addressed `vlv_` kernel-verification witness. Findings re-homed from
prover-lane whose proofs are still pending upstream PRs carry that note in their
caveats; a fresh `vlv_` gets attached once the proof merges into
google-deepmind/formal-conjectures.
