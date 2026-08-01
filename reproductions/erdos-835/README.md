# Erdős 835 exact replay

Proposal `vpr_08a91ee1b770f5cb` retains the exact proof and report.
`capsule.json` binds them to the current Proposal, Submission,
requirement-matching Verification, frozen source commit, Lean toolchain, and
Mathlib revision without changing any signed record.

Run the replay with a prepared checkout of
`google-deepmind/formal-conjectures`:

```bash
python3 reproductions/erdos-835/replay.py \
  --source ../formal-conjectures
```

The prepared checkout must contain the frozen Git object and the packages
named by its exact `lake-manifest.json`. Set
`VELA_FORMAL_CONJECTURES_SOURCE` instead of passing `--source` when integrating
this capsule with `vela reproduce`.

The current qualified replay requires macOS `sandbox-exec` and fails closed
when that network-isolation boundary is unavailable. A Linux runner must add
and qualify an equivalent native isolation profile before claiming replay
support.

The replay:

1. verifies every retained Proposal, Claim, signed Submission, Verification,
   Target, proof, report, and implementation root;
2. materializes source commit
   `85f863718beeec7b58a3a1926ee92e3472bc2020` in a temporary directory;
3. reconstructs the exact declaration splice from the retained proof bytes;
4. denies network access during the Lean build and kernel check; and
5. requires only `propext`, `Classical.choice`, and `Quot.sound`, with no
   `sorryAx` dependency for the target declaration.

It writes no Frontier record and has no authority or Standing effect. Kernel
acceptance does not prove Erdős problem 835, statement fidelity, novelty,
upstream acceptance, organizationally independent replication, or scientific
Standing.

Validate bindings without invoking Lean:

```bash
python3 reproductions/erdos-835/replay.py --validate-only
```
