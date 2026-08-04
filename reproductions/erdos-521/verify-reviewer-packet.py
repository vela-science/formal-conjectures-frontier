#!/usr/bin/env python3
"""Validate the Erdős 521 reviewer packet and reproduce its exact evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent
FRONTIER = ROOT.parents[1]
PACKET = ROOT / "reviewer-packet.v1.json"
REPORT = ROOT / "verification-report.v1.json"
EXPECTED_SCHEMA = "formal-conjectures.reviewer-packet.v1"
EXPECTED_PACKET_ID = "erdos-521-formal-proof-link"
PROOF_COMMIT = "4f915a323443bfb1709a6805a013812016dca88a"
PROOF_PROJECT = pathlib.Path("starfleet/erdos-521")
REQUIRED_TOP_LEVEL = {
    "schema",
    "packet_id",
    "purpose",
    "disposition",
    "triage",
    "source",
    "formal_conjectures",
    "external_proof",
    "statement_bridge",
    "verification",
    "frontier",
    "maintainer_decisions",
    "ai_assistance",
    "nonclaims",
    "reproduction",
}


class PacketError(RuntimeError):
    """The reviewer packet is incomplete or has drifted."""


def sha256(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(label: str, condition: bool) -> None:
    if not condition:
        raise PacketError(label)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-repo", type=pathlib.Path, required=True)
    parser.add_argument("--proof-repo", type=pathlib.Path, required=True)
    args = parser.parse_args()

    packet = json.loads(PACKET.read_text())
    require("wrong packet schema", packet.get("schema") == EXPECTED_SCHEMA)
    require("wrong packet id", packet.get("packet_id") == EXPECTED_PACKET_ID)
    require(
        "missing required packet sections",
        REQUIRED_TOP_LEVEL.issubset(packet),
    )
    require(
        "reviewer packet must remain non-authoritative",
        packet["frontier"]["authority_effect_of_packet"] == "none",
    )
    require(
        "maintainer decision list is incomplete",
        len(packet["maintainer_decisions"]) == 4,
    )
    require("nonclaims are incomplete", len(packet["nonclaims"]) >= 6)

    local_hashes = {
        packet["source"]["observation_path"]: packet["source"]["observation_sha256"],
        packet["statement_bridge"]["path"]: packet["statement_bridge"]["sha256"],
        packet["verification"]["script"]: packet["verification"]["script_sha256"],
        packet["verification"]["report"]: packet["verification"]["report_sha256"],
    }
    for relative, expected in local_hashes.items():
        observed = sha256(FRONTIER / relative)
        require(f"hash drift for {relative}: {observed}", observed == expected)

    proof_repo = args.proof_repo.resolve()
    with tempfile.TemporaryDirectory(prefix="erdos-521-review-") as temporary:
        checkout = pathlib.Path(temporary) / "lean-proofs"
        add = subprocess.run(
            [
                "git",
                "-C",
                str(proof_repo),
                "worktree",
                "add",
                "--detach",
                str(checkout),
                PROOF_COMMIT,
            ],
            text=True,
            capture_output=True,
            timeout=120,
        )
        if add.returncode != 0:
            raise PacketError(
                f"could not create pinned proof checkout\nstdout:\n{add.stdout}\nstderr:\n{add.stderr}"
            )
        try:
            cache = subprocess.run(
                ["lake", "exe", "cache", "get"],
                cwd=checkout / PROOF_PROJECT,
                text=True,
                capture_output=True,
                timeout=1800,
            )
            if cache.returncode != 0:
                raise PacketError(
                    f"could not hydrate pinned Mathlib cache\nstdout:\n{cache.stdout}\nstderr:\n{cache.stderr}"
                )
            command = [
                sys.executable,
                str(ROOT / "verify.py"),
                "--formal-repo",
                str(args.formal_repo.resolve()),
                "--proof-repo",
                str(checkout),
            ]
            result = subprocess.run(command, text=True, capture_output=True, timeout=1800)
            if result.returncode != 0:
                raise PacketError(
                    "evidence reproduction failed\n"
                    f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )
        finally:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(proof_repo),
                    "worktree",
                    "remove",
                    "--force",
                    str(checkout),
                ],
                text=True,
                capture_output=True,
                timeout=120,
            )
    reproduced = json.loads(result.stdout)
    retained = json.loads(REPORT.read_text())
    require("reproduced report differs from retained report", reproduced == retained)

    output = {
        "schema": "formal-conjectures.reviewer-packet-verification.v1",
        "ok": True,
        "packet_id": EXPECTED_PACKET_ID,
        "packet_sha256": sha256(PACKET),
        "evidence_report_sha256": sha256(REPORT),
        "dependency_closure": {
            "file_count": reproduced["proof"]["file_count"],
            "lean_file_count": reproduced["proof"]["lean_file_count"],
            "placeholder_hits": reproduced["proof"]["placeholder_hits"],
            "axiom_reports": reproduced["proof"]["axiom_reports"],
        },
        "statement_bridge": reproduced["statement_bridge"],
        "authority_effect": "none",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, PacketError, subprocess.TimeoutExpired) as error:
        print(f"reviewer packet verification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
