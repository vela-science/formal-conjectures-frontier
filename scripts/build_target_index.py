#!/usr/bin/env python3
"""Build and check the domain-owned current Target Index candidate.

The candidate carries only Formal Conjectures target semantics. Vela derives
Git identities, roots, packet sizes and packet digests when it seals the
candidate during repository migration or later maintenance.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

from validate_target_closure import (
    validate as validate_target_closure,
    validate_index as validate_closed_target_index,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANDIDATE_PATH = ROOT / ".vela" / "tmp" / "target-index-candidate.json"
INDEX_PATH = ROOT / "targets.json"
INPUT_PATHS = [
    "README.md",
    "SCOPE.md",
    "STATEMENT.md",
    "VELA.md",
    "scripts/build_target_index.py",
    "scripts/validate_target_closure.py",
    "targets/closures/formal-retain-erdos-424-correction.json",
    "targets/formal-retain-erdos-424-correction.json",
]


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
    validate_target_closure(ROOT)
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
        validate_target_closure(ROOT)
        validate_closed_target_index(ROOT)
    except ValueError as error:
        return [str(error)]
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
