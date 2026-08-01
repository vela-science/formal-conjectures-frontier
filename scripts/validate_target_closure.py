#!/usr/bin/env python3
"""Validate the completed Formal foreign-reference retention Target.

The closure is derived producer-work state. It confirms exact retention and
Verification while also proving that no foreign Claim entered local accepted
Standing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLOSURE_PATH = (
    ROOT / "targets" / "closures" / "formal-retain-erdos-424-correction.json"
)
LEAN_CLOSURE_PATH = (
    ROOT
    / "targets"
    / "closures"
    / "formal-erdos-835-property-iff-chromatic-number.json"
)
REPOSITORY_PATH = ROOT / ".vela" / "repository.json"
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class TargetClosureError(ValueError):
    """The derived Formal Target closure cannot be trusted."""


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def canonical_root(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_root(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(root: pathlib.Path, raw: str) -> pathlib.Path:
    path = pathlib.PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise TargetClosureError(f"unsafe Target closure path: {raw}")
    resolved = root.joinpath(*path.parts).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise TargetClosureError(f"Target closure path escapes the Frontier: {raw}")
    return resolved


def require_tracked(root: pathlib.Path, path: pathlib.Path) -> None:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise TargetClosureError(f"path escapes the Frontier: {path}") from error
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise TargetClosureError(f"Target closure input is untracked: {relative}")


def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise TargetClosureError(f"cannot read canonical JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise TargetClosureError(f"expected a JSON object at {path}")
    return value


def bound_json(
    root: pathlib.Path, path_raw: str, expected_root: str
) -> dict[str, Any]:
    if not SHA256_RE.fullmatch(expected_root):
        raise TargetClosureError(f"malformed SHA-256 root for {path_raw}")
    path = relative_path(root, path_raw)
    require_tracked(root, path)
    if not path.is_file():
        raise TargetClosureError(f"missing Target closure input: {path_raw}")
    observed = file_root(path)
    if observed != expected_root:
        raise TargetClosureError(
            f"Target closure root drift for {path_raw}: "
            f"expected {expected_root}, observed {observed}"
        )
    return read_json(path)


def evidence_by_kind(closure: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = closure.get("evidence")
    if not isinstance(rows, list):
        raise TargetClosureError("Target closure evidence is not a list")
    by_kind: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("kind"), str):
            raise TargetClosureError("Target closure contains malformed evidence")
        kind = row["kind"]
        if kind in by_kind:
            raise TargetClosureError(f"duplicate Target closure evidence kind: {kind}")
        by_kind[kind] = row
    required = {"claim", "proposal", "submission", "verification", "artifact"}
    if set(by_kind) != required:
        raise TargetClosureError(
            "Target closure evidence kinds differ: "
            f"expected {sorted(required)}, observed {sorted(by_kind)}"
        )
    return by_kind


def load_evidence(
    root: pathlib.Path, row: dict[str, Any], expected_id_field: str
) -> dict[str, Any]:
    value = bound_json(root, row.get("path", ""), row.get("root", ""))
    if value.get(expected_id_field) != row.get("id"):
        raise TargetClosureError(
            f"{row.get('kind')} evidence ID does not match {expected_id_field}"
        )
    return value


def validate(
    root: pathlib.Path = ROOT,
    closure_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    closure_path = (closure_path or root / CLOSURE_PATH.relative_to(ROOT)).resolve()
    repository_path = root / REPOSITORY_PATH.relative_to(ROOT)
    require_tracked(root, closure_path)
    require_tracked(root, repository_path)
    closure = read_json(closure_path)
    repository = read_json(repository_path)

    if closure.get("schema") != "vela.target-closure.v1":
        raise TargetClosureError("unsupported Target closure schema")
    if closure.get("frontier_id") != repository.get("frontier_id"):
        raise TargetClosureError("Target closure names another Frontier")
    if closure.get("target_id") != "formal:retain-erdos-424-correction":
        raise TargetClosureError("Target closure names another Target")
    if closure.get("status") != "closed":
        raise TargetClosureError("completed Target is not marked closed")
    if closure.get("successor_packet") is not None:
        raise TargetClosureError("closed retention Target invents a successor")
    closed_at_repository_root = closure.get("repository_root", "")
    if (
        not isinstance(closed_at_repository_root, str)
        or not closed_at_repository_root.startswith("sha256:")
        or len(closed_at_repository_root) != 71
    ):
        raise TargetClosureError("Target closure has no exact closure-time repository root")
    if canonical_root(closure.get("completion_contract")) != closure.get(
        "completion_contract_root"
    ):
        raise TargetClosureError("Target completion-contract root drifted")

    completed_packet = closure.get("completed_packet") or {}
    packet = bound_json(
        root, completed_packet.get("path", ""), completed_packet.get("sha256", "")
    )
    if packet.get("schema") != completed_packet.get("schema"):
        raise TargetClosureError("completed packet schema drifted")
    if packet.get("target") != closure.get("target_id"):
        raise TargetClosureError("completed packet names another Target")

    evidence = evidence_by_kind(closure)
    claim = load_evidence(root, evidence["claim"], "claim_id")
    proposal = load_evidence(root, evidence["proposal"], "proposal_id")
    submission = load_evidence(root, evidence["submission"], "submission_id")
    verification = load_evidence(
        root, evidence["verification"], "verification_record_id"
    )
    artifact_row = evidence["artifact"]
    artifact_path = relative_path(root, artifact_row.get("path", ""))
    require_tracked(root, artifact_path)
    if file_root(artifact_path) != artifact_row.get("root"):
        raise TargetClosureError("Target closure artifact root drifted")

    claim_id = evidence["claim"]["id"]
    claim_root = evidence["claim"]["root"]
    proposal_id = evidence["proposal"]["id"]
    submission_id = evidence["submission"]["id"]
    assertion = ((claim.get("assertion") or {}).get("text")) or ""
    if submission.get("claim", {}).get("assertion") != assertion:
        raise TargetClosureError("Submission and retained Claim assertions differ")
    if proposal.get("subject") != {
        "id": claim_id,
        "kind": "claim",
        "root": claim_root,
    }:
        raise TargetClosureError("Proposal does not bind the retained Claim")
    if artifact_row["root"] not in {
        row.get("digest") for row in submission.get("artifacts", [])
    }:
        raise TargetClosureError("Submission does not bind the retained archive")

    subject = verification.get("subject") or {}
    if verification.get("outcome") != "pass":
        raise TargetClosureError("Target closure Verification did not pass")
    if subject.get("claim_id") != claim_id:
        raise TargetClosureError("Verification does not bind the retained Claim")
    if subject.get("proposal_id") != proposal_id:
        raise TargetClosureError("Verification does not bind the Proposal")
    if subject.get("submission_id") != submission_id:
        raise TargetClosureError("Verification does not bind the Submission")
    if subject.get("submission_root") != evidence["submission"]["root"]:
        raise TargetClosureError("Verification binds a different Submission root")
    if artifact_row["root"].removeprefix("sha256:") not in subject.get(
        "artifact_ids", []
    ):
        raise TargetClosureError("Verification does not bind the retained archive")

    contract = closure["completion_contract"]
    if contract.get("artifact_sha256") != artifact_row["root"]:
        raise TargetClosureError("completion contract binds another archive")
    if contract.get("local_standing_effect") != "none":
        raise TargetClosureError("foreign retention claims local Standing effect")
    accepted_ids = {
        row.get("claim_id")
        for row in repository.get("accepted_claims", [])
        if isinstance(row, dict)
    }
    if claim_id in accepted_ids:
        raise TargetClosureError("foreign reference entered local accepted Standing")
    return {
        "schema": "formal-conjectures.target-closure-check.v1",
        "ok": True,
        "closed_target": closure["target_id"],
        "claim_root": claim_root,
        "submission_root": evidence["submission"]["root"],
        "verification_root": evidence["verification"]["root"],
        "artifact_root": artifact_row["root"],
        "local_standing_effect": "none",
    }


def validate_lean_proof(
    root: pathlib.Path = ROOT,
    closure_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    closure_path = (
        closure_path or root / LEAN_CLOSURE_PATH.relative_to(ROOT)
    ).resolve()
    repository_path = root / REPOSITORY_PATH.relative_to(ROOT)
    require_tracked(root, closure_path)
    require_tracked(root, repository_path)
    closure = read_json(closure_path)
    repository = read_json(repository_path)

    target_id = "formal:erdos-835-property-iff-chromatic-number"
    if closure.get("schema") != "vela.target-closure.v1":
        raise TargetClosureError("unsupported Lean Target closure schema")
    if closure.get("frontier_id") != repository.get("frontier_id"):
        raise TargetClosureError("Lean Target closure names another Frontier")
    if closure.get("target_id") != target_id:
        raise TargetClosureError("Lean Target closure names another Target")
    if closure.get("status") != "closed":
        raise TargetClosureError("completed Lean Target is not marked closed")
    if closure.get("successor_packet") is not None:
        raise TargetClosureError("closed Lean Target invents a successor")
    if not SHA256_RE.fullmatch(closure.get("repository_root", "")):
        raise TargetClosureError("Lean Target closure has no exact closure-time root")
    contract = closure.get("completion_contract")
    if canonical_root(contract) != closure.get("completion_contract_root"):
        raise TargetClosureError("Lean Target completion-contract root drifted")

    completed_packet = closure.get("completed_packet") or {}
    packet = bound_json(
        root, completed_packet.get("path", ""), completed_packet.get("sha256", "")
    )
    if packet.get("schema") != completed_packet.get("schema"):
        raise TargetClosureError("completed Lean packet schema drifted")
    if packet.get("target", {}).get("id") != target_id:
        raise TargetClosureError("completed Lean packet names another Target")

    evidence = evidence_by_kind_for(
        closure,
        {
            "claim",
            "proposal",
            "submission",
            "verification",
            "proof_artifact",
            "report_artifact",
        },
    )
    claim = load_evidence(root, evidence["claim"], "claim_id")
    proposal = load_evidence(root, evidence["proposal"], "proposal_id")
    submission = load_evidence(root, evidence["submission"], "submission_id")
    verification = load_evidence(
        root, evidence["verification"], "verification_record_id"
    )
    for kind in ("proof_artifact", "report_artifact"):
        row = evidence[kind]
        path = relative_path(root, row.get("path", ""))
        require_tracked(root, path)
        if file_root(path) != row.get("root"):
            raise TargetClosureError(f"{kind} root drifted")
        if row.get("id") != row.get("root", "").removeprefix("sha256:"):
            raise TargetClosureError(f"{kind} ID differs from its content root")

    claim_id = evidence["claim"]["id"]
    proposal_id = evidence["proposal"]["id"]
    submission_id = evidence["submission"]["id"]
    submission_root = evidence["submission"]["root"]
    if proposal.get("subject") != {
        "id": claim_id,
        "kind": "claim",
        "root": evidence["claim"]["root"],
    }:
        raise TargetClosureError("Lean Proposal does not bind the retained Claim")
    if proposal.get("producer_package") != {
        "id": submission_id,
        "kind": "submission_v1",
        "path": evidence["submission"]["path"],
        "root": submission_root,
    }:
        raise TargetClosureError("Lean Proposal does not bind the retained Submission")
    subject = verification.get("subject") or {}
    if verification.get("outcome") != "pass":
        raise TargetClosureError("Lean Target Verification did not pass")
    if subject.get("claim_id") != claim_id:
        raise TargetClosureError("Lean Verification does not bind the Claim")
    if subject.get("proposal_id") != proposal_id:
        raise TargetClosureError("Lean Verification does not bind the Proposal")
    if (
        subject.get("submission_id") != submission_id
        or subject.get("submission_root") != submission_root
    ):
        raise TargetClosureError("Lean Verification does not bind the Submission")
    artifact_ids = set(subject.get("artifact_ids", []))
    expected_artifacts = {
        evidence["proof_artifact"]["id"],
        evidence["report_artifact"]["id"],
    }
    if artifact_ids != expected_artifacts:
        raise TargetClosureError("Lean Verification artifact set differs")
    if verification.get("method", {}).get("profile") != contract.get(
        "verification_profile"
    ):
        raise TargetClosureError("Lean Verification profile differs")
    if contract.get("proof_sha256") != evidence["proof_artifact"]["root"]:
        raise TargetClosureError("Lean completion contract binds another proof")
    if contract.get("report_sha256") != evidence["report_artifact"]["root"]:
        raise TargetClosureError("Lean completion contract binds another report")
    if contract.get("producer_work_effect") != "closed":
        raise TargetClosureError("Lean completion contract leaves completed work open")
    if contract.get("accepted_state_change") != (
        "none until a separate authorized human Decision"
    ):
        raise TargetClosureError("Lean completion contract claims scientific authority")

    accepted_ids = {
        row.get("claim_id")
        for row in repository.get("accepted_claims", [])
        if isinstance(row, dict)
    }
    pending_ids = {
        row.get("claim_id")
        for row in repository.get("pending_claims", [])
        if isinstance(row, dict)
    }
    if claim_id in accepted_ids or claim_id not in pending_ids:
        raise TargetClosureError("Lean closure does not preserve pending review")
    if submission.get("claim", {}).get("assertion") != (
        (claim.get("assertion") or {}).get("text")
    ):
        raise TargetClosureError("Lean Submission and Claim assertions differ")
    return {
        "schema": "formal-conjectures.target-closure-check.v1",
        "ok": True,
        "closed_target": target_id,
        "claim_root": evidence["claim"]["root"],
        "submission_root": submission_root,
        "verification_root": evidence["verification"]["root"],
        "artifact_root": evidence["proof_artifact"]["root"],
        "local_standing_effect": "none",
    }


def evidence_by_kind_for(
    closure: dict[str, Any], required: set[str]
) -> dict[str, dict[str, Any]]:
    rows = closure.get("evidence")
    if not isinstance(rows, list):
        raise TargetClosureError("Target closure evidence is not a list")
    by_kind: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("kind"), str):
            raise TargetClosureError("Target closure contains malformed evidence")
        kind = row["kind"]
        if kind in by_kind:
            raise TargetClosureError(f"duplicate Target closure evidence kind: {kind}")
        by_kind[kind] = row
    if set(by_kind) != required:
        raise TargetClosureError(
            "Target closure evidence kinds differ: "
            f"expected {sorted(required)}, observed {sorted(by_kind)}"
        )
    return by_kind


def validate_all(root: pathlib.Path = ROOT) -> list[dict[str, Any]]:
    return [validate(root), validate_lean_proof(root)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        results = validate_all()
    except TargetClosureError as error:
        if args.json:
            print(
                json.dumps(
                    {
                        "schema": "formal-conjectures.target-closure-check.v1",
                        "ok": False,
                        "error": str(error),
                    },
                    sort_keys=True,
                )
            )
        else:
            print(f"Target closure invalid: {error}")
        return 1
    if args.json:
        print(
            json.dumps(
                {
                    "schema": "formal-conjectures.target-closure-set-check.v1",
                    "ok": True,
                    "closures": results,
                },
                sort_keys=True,
            )
        )
    else:
        print(
            "Target closures valid: "
            + ", ".join(result["closed_target"] for result in results)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
