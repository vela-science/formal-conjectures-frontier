# Erdős 521 frontier-to-commons disposition

## Disposition

**Upstream the source statement and pinned external proof link through existing
Formal Conjectures PR 4578. Keep the 151-file proof corpus external.**

This is the second explicit frontier-to-commons disposition. Formal
Conjectures is the native owner of the benchmark statement and
`formal_proof` metadata. The proof repository remains the native owner of the
proof and its build. Copying that proof into Formal Conjectures would duplicate
more than one megabyte of source, cross a different Lean and Mathlib boundary,
and violate the statement repository's preference for short statements and
external links.

The reviewer packet is
[`reviewer-packet.v1.json`](reviewer-packet.v1.json). It is useful without
Vela: it binds the source observation, exact pull-request blob, proof subtree,
statement bridge, toolchain, axiom set, import footprint, native checks,
attribution, nonclaims, and the remaining maintainer decisions.

## Exact contribution under review

- Native owner: `google-deepmind/formal-conjectures`
- Pull request: `https://github.com/google-deepmind/formal-conjectures/pull/4578`
- Pull-request commit: `a3b9c2fef2e5c6dbe1652642c7429abdfbd21c5b`
- Source path: `FormalConjectures/ErdosProblems/521.lean`
- Source blob: `b1b346fc31d9332afcd1681630b85196e5cd289a`
- Declaration: `Erdos521.erdos_521`
- Proposed statement: `answer(False) ↔ Erdos521.Claim`
- External proof commit: `4f915a323443bfb1709a6805a013812016dca88a`
- External proof subtree: `1ce5783dcf0c167eb521996dafa48a7b50a44a57`
- Stable proof entry: `Research.Erdos521`
- Terminal theorem: `Erdos521.erdos_521_negative : ¬ Erdos521.Claim`
- Lean: `leanprover/lean4:v4.31.0`
- Mathlib: `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`
- Axioms: `propext`, `Classical.choice`, and `Quot.sound`

The accepted local qualification is Claim
`vcl_a183a1e5d9f461d8ec5fa35b1e75a25c67f75b7278d30ebf83af8e9c53ab48ea`.
Verification `vvr_579130c4b713c073` reproduces the source blob, proof subtree,
stable build, statement bridge, and axiom set. Decision
`vev_57e929bead5143e7` accepts only that exact bounded qualification in the
Formal Conjectures Frontier.

## Dependency issue exposed before review

The PR description says its automated link check reads each linked file but
not its imports. That is insufficient for a formal-proof link: a clean terminal
file can depend on a placeholder, declared axiom, or unsafe escape elsewhere
in its import closure.

The source-local verifier closes that gap for this case. It binds the complete
154-file proof subtree, scans all 151 Lean files for `sorry`, `admit`, `axiom`,
and `unsafe`, builds the stable `Research.Erdos521` entry, compiles the terminal
theorem, and requires the exact permitted axiom set. This does not prove a
general link-auditing method; it gives the reviewer complete dependency
evidence for this one link.

## Statement-fidelity issue requiring a maintainer decision

The current source says “number of real roots” without saying whether roots are
counted with multiplicity. Both the PR statement and the external proof use
`Polynomial.rootSet`, so they count distinct roots. The compiled bridge proves
that the two formal Claims are equal under that interpretation. It cannot
decide whether the interpretation is the intended informal statement.

The source also records historical ambiguity between coefficients in
`{0,1}` and `{-1,1}`. The candidate follows the current displayed
`{-1,1}` statement and makes no claim about the other interpretation.

## Reviewer decisions still needed

1. Is distinct-root counting the intended interpretation of `R_n`?
2. Is `research solved` appropriate while the Erdős Problems source remains
   `OPEN` but records a claimed solution?
3. Is the attribution to prior solvers and Star Fleet Math sufficient?
4. Is a pinned external proof link acceptable with the complete dependency
   closure kept in a separate repository and toolchain?

These are native maintainer decisions. Local Vela Standing does not answer
them and is not evidence of upstream acceptance.

## Nonclaims

- PR 4578 remains open and has not been accepted by Formal Conjectures.
- The official Erdős Problems status remains open.
- No novelty, priority, or external mathematical review is established.
- The alternative `{0,1}` coefficient interpretation is not resolved.
- A multiplicity-sensitive root-count statement is not established.
- The shared operator, machine, source, proof bytes, Lean kernel, and Mathlib
  dependencies remain explicit.
- This case does not establish a general Vela productivity or adoption result.

## Reproduction

```bash
cd <formal-conjectures-frontier>
python3 reproductions/erdos-521/verify-reviewer-packet.py \
  --formal-repo <formal-conjectures> \
  --proof-repo <lean-proofs>
```

This document and its packet are read artifacts. They create no Vela Claim,
Verification, Decision, external review state, or authority effect.
