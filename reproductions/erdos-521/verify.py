#!/usr/bin/env python3
"""Reproduce the exact Erdős 521 proof and statement bridge."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Sequence


ROOT = pathlib.Path(__file__).resolve().parent
FORMAL_COMMIT = "a3b9c2fef2e5c6dbe1652642c7429abdfbd21c5b"
FORMAL_PATH = "FormalConjectures/ErdosProblems/521.lean"
FORMAL_BLOB = "b1b346fc31d9332afcd1681630b85196e5cd289a"
FORMAL_SHA256 = "d165750c9a5168f432f945f57cc9e58daf4d656e489c79c9744e55aec422b9e3"
PROOF_COMMIT = "4f915a323443bfb1709a6805a013812016dca88a"
PROOF_SUBTREE = "1ce5783dcf0c167eb521996dafa48a7b50a44a57"
PROOF_ROOT = "starfleet/erdos-521"
MATHLIB_COMMIT = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
PLACEHOLDER = re.compile(r"\b(?:sorry|admit|axiom|unsafe)\b")
AXIOMS = re.compile(r"depends on axioms: \[([^]]*)\]")


class VerificationError(RuntimeError):
    """The frozen qualification boundary did not reproduce."""


def run(
    args: Sequence[str],
    *,
    cwd: pathlib.Path,
    timeout: int = 1200,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise VerificationError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def git(repo: pathlib.Path, *args: str) -> str:
    return run(["git", *args], cwd=repo, timeout=120).stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_equal(label: str, observed: object, expected: object) -> None:
    if observed != expected:
        raise VerificationError(f"{label} drift: expected {expected!r}, observed {observed!r}")


def commit_bytes(repo: pathlib.Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repo,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise VerificationError(
            f"cannot read {commit}:{path}: {result.stderr.decode(errors='replace')}"
        )
    return result.stdout


def parse_axiom_sets(output: str) -> list[list[str]]:
    sets: list[list[str]] = []
    for match in AXIOMS.finditer(output):
        values = [value.strip() for value in match.group(1).split(",") if value.strip()]
        sets.append(values)
    return sets


def verify_axioms(label: str, output: str, minimum_reports: int) -> list[list[str]]:
    if "sorryAx" in output:
        raise VerificationError(f"{label} depends on sorryAx")
    reports = parse_axiom_sets(output)
    if len(reports) < minimum_reports:
        raise VerificationError(f"{label} emitted only {len(reports)} axiom reports")
    for report in reports:
        require_equal(f"{label} axiom set", set(report), ALLOWED_AXIOMS)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--formal-repo",
        type=pathlib.Path,
        default=ROOT.parents[2] / "formal-conjectures",
    )
    parser.add_argument(
        "--proof-repo",
        type=pathlib.Path,
        default=ROOT.parents[2] / "lean-proofs",
    )
    args = parser.parse_args()
    formal_repo = args.formal_repo.resolve()
    proof_repo = args.proof_repo.resolve()
    proof_project = proof_repo / PROOF_ROOT

    formal_blob = git(formal_repo, "rev-parse", f"{FORMAL_COMMIT}:{FORMAL_PATH}").strip()
    require_equal("Formal Conjectures blob", formal_blob, FORMAL_BLOB)
    formal_bytes = commit_bytes(formal_repo, FORMAL_COMMIT, FORMAL_PATH)
    require_equal("Formal Conjectures file SHA-256", sha256(formal_bytes), FORMAL_SHA256)

    proof_commit = git(proof_repo, "rev-parse", "HEAD").strip()
    require_equal("proof repository HEAD", proof_commit, PROOF_COMMIT)
    proof_tree = git(proof_repo, "rev-parse", f"{PROOF_COMMIT}:{PROOF_ROOT}").strip()
    require_equal("proof subtree", proof_tree, PROOF_SUBTREE)
    if git(proof_repo, "status", "--porcelain", "--", PROOF_ROOT).strip():
        raise VerificationError("proof subtree has tracked or untracked worktree changes")

    proof_files = git(
        proof_repo, "ls-tree", "-r", "--name-only", PROOF_COMMIT, "--", PROOF_ROOT
    ).splitlines()
    lean_files = [path for path in proof_files if path.endswith(".lean")]
    placeholder_hits: list[str] = []
    for path in lean_files:
        text = commit_bytes(proof_repo, PROOF_COMMIT, path).decode("utf-8")
        if PLACEHOLDER.search(text):
            placeholder_hits.append(path)
    require_equal("proof placeholder hits", placeholder_hits, [])

    manifest = json.loads((proof_project / "lake-manifest.json").read_text())
    mathlib = next(package for package in manifest["packages"] if package["name"] == "mathlib")
    require_equal("Mathlib revision", mathlib["rev"], MATHLIB_COMMIT)
    toolchain = (proof_project / "lean-toolchain").read_text().strip()
    require_equal("Lean toolchain", toolchain, "leanprover/lean4:v4.31.0")

    build = run(["lake", "build", "Research.Erdos521"], cwd=proof_project)
    check = run(["lake", "env", "lean", "Check.lean"], cwd=proof_project)
    check_output = check.stdout + check.stderr
    proof_axioms = verify_axioms("terminal theorem", check_output, 1)

    bridge_path = ROOT / "StatementBridge.lean"
    bridge = run(
        ["lake", "env", "lean", str(bridge_path)],
        cwd=proof_project,
    )
    bridge_output = bridge.stdout + bridge.stderr
    bridge_axioms = verify_axioms("statement bridge", bridge_output, 3)

    source_path = ROOT / "source-observation.md"
    result = {
        "schema": "formal-conjectures.erdos-521-verification.v1",
        "ok": True,
        "formal_conjectures": {
            "commit": FORMAL_COMMIT,
            "path": FORMAL_PATH,
            "git_blob": FORMAL_BLOB,
            "file_sha256": "sha256:" + FORMAL_SHA256,
        },
        "proof": {
            "commit": PROOF_COMMIT,
            "subtree": PROOF_SUBTREE,
            "file_count": len(proof_files),
            "lean_file_count": len(lean_files),
            "placeholder_hits": placeholder_hits,
            "lean_toolchain": toolchain,
            "mathlib_commit": MATHLIB_COMMIT,
            "terminal_module": "Research.Erdos521",
            "terminal_theorem": "Erdos521.erdos_521_negative : ¬ Erdos521.Claim",
            "axiom_reports": proof_axioms,
            "build_status": "pass",
        },
        "statement_bridge": {
            "path": bridge_path.relative_to(ROOT.parents[1]).as_posix(),
            "sha256": "sha256:" + sha256(bridge_path.read_bytes()),
            "claim_equivalence": "FormalConjecturesErdos521.Claim ↔ Erdos521.Claim",
            "negative_theorem": "FormalConjecturesErdos521.negative",
            "axiom_reports": bridge_axioms,
        },
        "source_observation": {
            "path": source_path.relative_to(ROOT.parents[1]).as_posix(),
            "sha256": "sha256:" + sha256(source_path.read_bytes()),
        },
        "shared_dependencies": [
            "Same operator and machine as the producer-side inspection.",
            "Same pinned lean-proofs corpus, Lean kernel, and Mathlib revision.",
            "Formal Conjectures source is an open pull-request commit, not an upstream merge.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, VerificationError, subprocess.TimeoutExpired) as error:
        print(f"erdos-521 verification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
