#!/usr/bin/env python3
"""Build the domain-owned Target Index v2 candidate.

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

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANDIDATE_PATH = ROOT / ".vela" / "tmp" / "target-index-candidate.json"
INDEX_PATH = ROOT / "targets.json"
PACKET_PATH = ROOT / "targets" / "formal-erdos-505-test-dim-one.json"
INPUT_PATHS = [
    "README.md",
    "SCOPE.md",
    "STATEMENT.md",
    "scripts/build_target_index.py",
]
TARGET = {
    "id": "formal:erdos-505-test-dim-one",
    "title": "Prove the one-dimensional test case of Erdős 505 in Lean",
    "why": (
        "Frozen upstream main leaves the exact category-test theorem "
        "sorry-backed; the primary Erdős record calls the one-dimensional "
        "case trivial, and no open pull request claims problem 505."
    ),
    "state": "open",
    "rank": 1,
    "objective": (
        "Produce one sorry-free proof term that the frozen Lean kernel accepts "
        "for the exact upstream theorem statement."
    ),
    "labels": [
        "collision-checked",
        "formal-conjectures",
        "kernel-check",
        "lean4",
        "upstream-sorry",
    ],
    "packet": {
        "path": "targets/formal-erdos-505-test-dim-one.json",
        "schema": "formal-conjectures.lean-proof-work.v1",
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


def candidate() -> dict[str, Any]:
    return {
        "schema": "vela.target-index-candidate.v1",
        "frontier_id": "vfr_97d7d25957384f80",
        "source": {
            "git_commit": git_head(),
            "input_paths": INPUT_PATHS,
        },
        "targets": [TARGET],
    }


def packet_root() -> str:
    return "sha256:" + hashlib.sha256(PACKET_PATH.read_bytes()).hexdigest()


def check() -> list[str]:
    failures: list[str] = []
    sealed = json.loads(INDEX_PATH.read_text())
    if sealed.get("schema") != "vela.target-index.v2":
        return ["targets.json is not a sealed vela.target-index.v2"]
    actual = sealed.get("targets", [])
    if len(actual) != 1:
        return [f"targets.json has {len(actual)} targets; expected 1"]
    expected = TARGET
    row = actual[0]
    for key, value in expected.items():
        if key != "packet" and row.get(key) != value:
            failures.append(f"targets.json differs at {key}")
    packet = row.get("packet", {})
    if packet.get("path") != expected["packet"]["path"]:
        failures.append("targets.json packet path differs")
    if packet.get("schema") != expected["packet"]["schema"]:
        failures.append("targets.json packet schema differs")
    if packet.get("size") != PACKET_PATH.stat().st_size:
        failures.append("targets.json packet size differs")
    if packet.get("sha256") != packet_root():
        failures.append("targets.json packet digest differs")
    return failures


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
        print("Target Index v2 is current.")
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
