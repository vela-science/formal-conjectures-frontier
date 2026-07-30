#!/usr/bin/env python3
"""Build and check the domain-owned current Target Index candidate.

The candidate carries only Formal Conjectures target semantics. Vela derives
Git identities, roots, packet sizes and packet digests when it seals the
candidate during repository migration or later maintenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Any

from validate_target_closure import (
    validate_all as validate_target_closures,
    validate_index as validate_closed_target_index,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANDIDATE_PATH = ROOT / ".vela" / "tmp" / "target-index-candidate.json"
INDEX_PATH = ROOT / "targets.json"
PACKET_PATH = (
    ROOT / "targets" / "formal-erdos-835-property-iff-chromatic-number.json"
)
TARGET_ID = "formal:erdos-835-property-iff-chromatic-number"
PACKET_SCHEMA = "formal-conjectures.lean-proof-work.v1"
UPSTREAM_COMMIT = "85f863718beeec7b58a3a1926ee92e3472bc2020"
UPSTREAM_TREE = "e14c3d6b1b1fc5e378e72398cb9a402dd981db63"
SOURCE_FILE_ROOT = (
    "sha256:f163f1f5a6fead133f3a66ae400305fcb40c6019321ce21e869ce5b3c0ab89a0"
)
DECLARATION_SPAN_ROOT = (
    "sha256:82ecd5e20d93c83d348f3b473e55375fca272b380fe9259f68e7796c3b0b09ff"
)
TOOLCHAIN_ROOT = (
    "sha256:e695e6e5d8e7a8be4d6cf159dfb995847993d26c6cc450353a86f387279025b9"
)
MANIFEST_ROOT = (
    "sha256:5b99b5f4f807cbba67bbcd22e5e486c17d6a8d970ea218de08d05830ab350c26"
)
MATHLIB_COMMIT = "a3a10db0e9d66acbebf76c5e6a135066525ac900"
FROZEN_REPOSITORY_ROOT = (
    "sha256:5e59e05a5639ac0ec4331ec40fec9f50229b795a1a08d983ba96834d4777b58a"
)
INPUT_PATHS = [
    "README.md",
    "SCOPE.md",
    "STATEMENT.md",
    "VELA.md",
    "scripts/build_target_index.py",
    "scripts/validate_target_closure.py",
    "targets/closures/formal-erdos-835-property-iff-chromatic-number.json",
    "targets/closures/formal-retain-erdos-424-correction.json",
    "targets/formal-retain-erdos-424-correction.json",
    "tests/test_target_closure.py",
    "tests/test_target_index.py",
]
TARGET = {
    "id": TARGET_ID,
    "title": "Prove the Erdős 835 property/chromatic-number equivalence",
    "why": (
        "The exact category-test declaration remains sorry-backed at the "
        "frozen official source revision, has a bounded kernel verifier, and "
        "had no exact solution or semantic pull-request collision at freeze."
    ),
    "state": "open",
    "rank": 1,
    "objective": (
        "Produce one sorry-free Lean proof term for the exact frozen "
        "Erdos835.property_iff_chromaticNumber declaration."
    ),
    "labels": [
        "collision-checked",
        "formal-conjectures",
        "kernel-check",
        "lean4",
        "no-answer-leak",
    ],
    "packet": {
        "path": "targets/formal-erdos-835-property-iff-chromatic-number.json",
        "schema": PACKET_SCHEMA,
    },
}


def git_head() -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD^{commit}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def sha256_root(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def file_root(path: pathlib.Path) -> str:
    return sha256_root(path.read_bytes())


def validate_packet(packet: dict[str, Any] | None = None) -> None:
    if packet is None:
        packet = json.loads(PACKET_PATH.read_text())
    expected_fields = {
        "authority",
        "budget",
        "environment",
        "frontier",
        "input_policy",
        "limitations",
        "output_contract",
        "schema",
        "selection",
        "source",
        "target",
        "verification",
    }
    if set(packet) != expected_fields:
        raise ValueError("formal proof packet fields are not the closed mission set")
    if packet["schema"] != PACKET_SCHEMA:
        raise ValueError("formal proof packet schema differs from the Target")
    if packet["frontier"] != {
        "frontier_id": "vfr_97d7d25957384f80",
        "repository_root": FROZEN_REPOSITORY_ROOT,
    }:
        raise ValueError("formal proof packet differs from its frozen Frontier context")
    if packet["target"] != {
        "id": TARGET_ID,
        "state": "open",
        "objective": TARGET["objective"],
    }:
        raise ValueError("formal proof packet target semantics differ")

    source = packet["source"]
    if source["git_commit"] != UPSTREAM_COMMIT or source["git_tree"] != UPSTREAM_TREE:
        raise ValueError("formal proof packet upstream revision differs")
    if source["file_sha256"] != SOURCE_FILE_ROOT:
        raise ValueError("formal proof packet source-file root differs")
    if source["declaration"] != "Erdos835.property_iff_chromaticNumber":
        raise ValueError("formal proof packet declaration differs")
    if (
        source["declaration_span_sha256"] != DECLARATION_SPAN_ROOT
        or sha256_root(source["declaration_span"].encode()) != DECLARATION_SPAN_ROOT
    ):
        raise ValueError("formal proof packet declaration-span root differs")

    environment = packet["environment"]
    if environment != {
        "lean_version": "4.27.0",
        "lean_toolchain": "leanprover/lean4:v4.27.0",
        "lean_toolchain_sha256": TOOLCHAIN_ROOT,
        "lake_manifest_sha256": MANIFEST_ROOT,
        "mathlib_git_commit": MATHLIB_COMMIT,
    }:
        raise ValueError("formal proof packet environment differs")
    if sha256_root(environment["lean_toolchain"].encode()) != TOOLCHAIN_ROOT:
        raise ValueError("formal proof packet Lean toolchain root differs")
    if packet["budget"] != {
        "compute": "cpu_only",
        "network": "denied",
        "maximum_wall_time_seconds": 3600,
    }:
        raise ValueError("formal proof packet budget differs")

    output = packet["output_contract"]
    if (
        output["schema"] != "canopus.lean-proof-term.v1"
        or output["kind"] != "lean-proof"
        or output["path"]
        != "artifacts/erdos835-property-iff-chromatic-number-proof.lean"
        or output["maximum_bytes"] != 131072
    ):
        raise ValueError("formal proof packet output contract differs")
    excluded = "\n".join(packet["input_policy"]["excluded_answer_sources"])
    for required in ("golden", "candidate proofs", "Pull-request", "network"):
        if required not in excluded:
            raise ValueError("formal proof packet answer-leak exclusions differ")

    axioms = packet["verification"]["axioms"]
    if axioms != {
        "allowed": ["propext", "Classical.choice", "Quot.sound"],
        "forbidden": ["sorryAx"],
    }:
        raise ValueError("formal proof packet axiom policy differs")
    if packet["authority"] != {
        "producer_ceiling": "pending_review",
        "verification_ceiling": "evidence_only",
        "accepted_standing_effect": "none",
        "requires_human_decision": True,
        "human_key_access": "forbidden",
    }:
        raise ValueError("formal proof packet authority ceiling differs")
    if len(packet["limitations"]) != 4:
        raise ValueError("formal proof packet limitations differ")

    collision = packet["selection"]["live_collision_check"]
    if collision["remote_head"] != UPSTREAM_COMMIT:
        raise ValueError("formal proof packet collision check observed another HEAD")
    if collision["exact_solution_matches"] or collision["exact_declaration_open_pr_matches"]:
        raise ValueError("formal proof packet records an exact solution collision")
    source_prs = collision["source_file_open_prs"]
    if source_prs != [
        {
            "number": 4004,
            "head_commit": "a77dee7db6b14ceb53aeb86bfedde832148f7ee5",
            "url": "https://github.com/google-deepmind/formal-conjectures/pull/4004",
            "disposition": "non_semantic_docstring_markup",
            "declaration_span_changed": False,
        },
        {
            "number": 4631,
            "head_commit": "0a789bb3adc31b158966ef3b84e9b82fb703575e",
            "url": "https://github.com/google-deepmind/formal-conjectures/pull/4631",
            "disposition": "non_semantic_module_migration",
            "declaration_span_changed": False,
        },
    ]:
        raise ValueError("formal proof packet source-file PR disposition differs")


def candidate() -> dict[str, Any]:
    validate_target_closures(ROOT)
    validate_packet()
    return {
        "schema": "vela.target-index-candidate.v1",
        "frontier_id": "vfr_97d7d25957384f80",
        "source": {
            "git_commit": git_head(),
            "input_paths": INPUT_PATHS,
        },
        "targets": [],
    }


def check() -> list[str]:
    try:
        validate_target_closures(ROOT)
        validate_closed_target_index(ROOT)
        validate_packet()
    except ValueError as error:
        return [str(error)]
    sealed = json.loads(INDEX_PATH.read_text())
    targets = sealed.get("targets", [])
    if targets:
        return [f"targets.json has {len(targets)} targets; expected 0"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=CANDIDATE_PATH,
        help=(
            "candidate path; repository migration requires a path outside "
            "the frontier checkout"
        ),
    )
    args = parser.parse_args()
    if args.check:
        failures = check()
        if failures:
            print("\n".join(failures), file=sys.stderr)
            return 1
        print("Target Index v4 is current.")
        return 0
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(candidate()))
    try:
        display = output.relative_to(ROOT)
    except ValueError:
        display = output
    print(f"Wrote {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
