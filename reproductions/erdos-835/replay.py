#!/usr/bin/env python3
"""Replay the exact retained Erdős 835 Lean proof without changing Standing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


CAPSULE_DIR = Path(__file__).resolve().parent
DEFAULT_FRONTIER = CAPSULE_DIR.parents[1]
CAPSULE_PATH = CAPSULE_DIR / "capsule.json"
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_PROOF_TOKEN_RE = re.compile(r"\b(sorry|admit|axiom|unsafe)\b")


class ReplayError(RuntimeError):
    """A fail-closed replay error."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise ReplayError(f"read JSON {path}: {error}") from error


def resolve_frontier_file(frontier: Path, relative: str) -> Path:
    if not relative or relative.startswith("/"):
        raise ReplayError(f"capsule path is not relative: {relative!r}")
    candidate = frontier / relative
    if candidate.is_symlink():
        raise ReplayError(f"capsule path may not be a symlink: {relative}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(frontier)
    except (FileNotFoundError, ValueError) as error:
        raise ReplayError(f"capsule path escapes or is missing: {relative}") from error
    if not resolved.is_file():
        raise ReplayError(f"capsule path is not a file: {relative}")
    return resolved


def verify_rooted_file(frontier: Path, reference: dict[str, Any]) -> Path:
    path = resolve_frontier_file(frontier, reference["path"])
    expected = reference["sha256"]
    if not SHA256_RE.fullmatch(expected):
        raise ReplayError(f"invalid expected SHA-256 for {reference['path']}")
    observed = sha256_bytes(path.read_bytes())
    if observed != expected:
        raise ReplayError(
            f"{reference['path']} root differs: expected {expected}, observed {observed}"
        )
    return path


def require_equal(actual: Any, expected: Any, subject: str) -> None:
    if actual != expected:
        raise ReplayError(f"{subject} differs: expected {expected!r}, observed {actual!r}")


def validate_capsule(frontier: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    frontier = frontier.resolve(strict=True)
    capsule = load_json(CAPSULE_PATH)
    require_equal(
        capsule.get("schema"),
        "formal-conjectures.lean-replay-capsule.v1",
        "capsule schema",
    )
    require_equal(capsule.get("authority"), "evidence_only", "capsule authority")
    require_equal(capsule.get("standing_effect"), "none", "capsule Standing effect")

    paths: dict[str, Path] = {}
    for name in (
        "proposal",
        "claim",
        "submission",
        "registration",
        "verification",
        "target_packet",
        "target_closure",
        "proof",
        "attempt_report",
        "implementation",
    ):
        paths[name] = verify_rooted_file(frontier, capsule["inputs"][name])

    proposal = load_json(paths["proposal"])
    claim = load_json(paths["claim"])
    submission = load_json(paths["submission"])
    registration = load_json(paths["registration"])
    verification = load_json(paths["verification"])
    packet = load_json(paths["target_packet"])
    closure = load_json(paths["target_closure"])
    report = load_json(paths["attempt_report"])

    identity = capsule["identity"]
    require_equal(proposal["proposal_id"], identity["proposal_id"], "Proposal id")
    require_equal(
        proposal["subject"]["id"], identity["claim_id"], "Proposal Claim id"
    )
    require_equal(
        proposal["subject"]["root"],
        capsule["inputs"]["claim"]["sha256"],
        "Proposal Claim root",
    )
    require_equal(
        proposal["producer_package"]["id"],
        identity["submission_id"],
        "Proposal Submission id",
    )
    require_equal(
        proposal["producer_package"]["root"],
        capsule["inputs"]["submission"]["sha256"],
        "Proposal Submission root",
    )
    require_equal(claim["claim_id"], identity["claim_id"], "Claim id")
    require_equal(
        submission["submission_id"], identity["submission_id"], "Submission id"
    )
    require_equal(
        registration["registration_record_id"],
        identity["registration_record_id"],
        "Registration id",
    )
    require_equal(
        registration["proposal_id"], identity["proposal_id"], "Registration Proposal"
    )
    require_equal(
        registration["submission_id"],
        identity["submission_id"],
        "Registration Submission",
    )
    require_equal(
        verification["verification_record_id"],
        identity["verification_record_id"],
        "Verification id",
    )
    require_equal(
        verification["subject"]["proposal_id"],
        identity["proposal_id"],
        "Verification Proposal",
    )
    require_equal(
        verification["subject"]["submission_id"],
        identity["submission_id"],
        "Verification Submission",
    )
    require_equal(
        verification["subject"]["claim_id"],
        identity["claim_id"],
        "Verification Claim",
    )
    require_equal(verification["outcome"], "pass", "Verification outcome")
    require_equal(
        verification["scope"]["property"],
        capsule["verification_requirement"],
        "Verification property",
    )

    proof_reference = capsule["inputs"]["proof"]
    report_reference = capsule["inputs"]["attempt_report"]
    submitted_artifacts = {
        (item["kind"], item["digest"]) for item in submission["artifacts"]
    }
    if ("lean-proof", proof_reference["sha256"]) not in submitted_artifacts:
        raise ReplayError("Submission does not bind the exact retained Lean proof")
    if ("verification-report", report_reference["sha256"]) not in submitted_artifacts:
        raise ReplayError("Submission does not bind the exact retained attempt report")

    require_equal(
        packet["schema"],
        "formal-conjectures.lean-proof-work.v1",
        "Target packet schema",
    )
    require_equal(packet["target"]["id"], identity["target_id"], "Target id")
    require_equal(
        closure["target_id"], identity["target_id"], "Target closure id"
    )
    require_equal(closure["status"], "closed", "Target closure status")
    require_equal(
        closure["completion_contract"]["proof_sha256"],
        proof_reference["sha256"],
        "Target closure proof root",
    )
    require_equal(
        closure["completion_contract"]["report_sha256"],
        report_reference["sha256"],
        "Target closure report root",
    )

    source = capsule["source"]
    for key in (
        "repository",
        "git_commit",
        "git_tree",
        "path",
        "file_sha256",
        "declaration",
        "declaration_span_sha256",
    ):
        require_equal(packet["source"][key], source[key], f"Target source {key}")
    require_equal(
        packet["source"]["declaration_span"],
        source["declaration_span"],
        "Target declaration span",
    )
    for key in (
        "lean_version",
        "lean_toolchain_sha256",
        "lake_manifest_sha256",
        "mathlib_git_commit",
    ):
        require_equal(
            packet["environment"][key],
            capsule["environment"][key],
            f"Target environment {key}",
        )

    require_equal(
        report["artifact"]["sha256"], proof_reference["sha256"], "Report proof root"
    )
    require_equal(
        report["verification"]["verification_source_sha256"],
        capsule["expected"]["verification_source_sha256"],
        "Report verification-source root",
    )
    require_equal(
        report["verification"]["axioms"],
        capsule["expected"]["axioms"],
        "Report axiom set",
    )
    require_equal(
        report["verification"]["sorryAx_present"],
        False,
        "Report target sorryAx state",
    )

    proof_bytes = paths["proof"].read_bytes()
    if len(proof_bytes) > packet["output_contract"]["maximum_bytes"]:
        raise ReplayError("retained proof exceeds the frozen byte ceiling")
    if not proof_bytes.startswith(b"by\n"):
        raise ReplayError("retained proof does not begin with `by`")
    proof_text = proof_bytes.decode("utf-8")
    if FORBIDDEN_PROOF_TOKEN_RE.search(proof_text):
        raise ReplayError("retained proof contains a forbidden token")
    if "import " in proof_text or "```" in proof_text:
        raise ReplayError("retained proof contains a forbidden wrapper")

    return capsule, paths


def git_output(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ReplayError(
            f"git {' '.join(arguments)} failed in {repository}: "
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def prepared_source(arguments: argparse.Namespace, frontier: Path) -> Path:
    candidates: list[Path] = []
    if arguments.source:
        candidates.append(arguments.source)
    if os.environ.get("VELA_FORMAL_CONJECTURES_SOURCE"):
        candidates.append(Path(os.environ["VELA_FORMAL_CONJECTURES_SOURCE"]))
    candidates.append(frontier.parent / "formal-conjectures")
    for candidate in candidates:
        if (candidate / ".git").exists() and (candidate / ".lake/packages").is_dir():
            return candidate.resolve()
    raise ReplayError(
        "no prepared Formal Conjectures checkout found; pass --source or set "
        "VELA_FORMAL_CONJECTURES_SOURCE to a Git checkout with its exact "
        "lake-manifest packages available"
    )


def extract_exact_source(
    source_repository: Path, destination: Path, commit: str
) -> None:
    archive = subprocess.Popen(
        [
            "git",
            "-C",
            str(source_repository),
            "archive",
            "--format=tar",
            commit,
        ],
        stdout=subprocess.PIPE,
    )
    if archive.stdout is None:
        raise ReplayError("git archive did not expose stdout")
    try:
        extraction = subprocess.run(
            ["tar", "-x", "-C", str(destination)],
            stdin=archive.stdout,
            check=False,
            capture_output=True,
            text=False,
        )
    finally:
        archive.stdout.close()
    if archive.wait() != 0 or extraction.returncode != 0:
        raise ReplayError("git archive failed for the frozen source commit")


def network_denied_command(command: list[str]) -> list[str]:
    sandbox = Path("/usr/bin/sandbox-exec")
    if not sandbox.is_file():
        raise ReplayError(
            "this replay requires macOS sandbox-exec for fail-closed network denial"
        )
    return [
        str(sandbox),
        "-p",
        "(version 1) (allow default) (deny network*)",
        *command,
    ]


def run_checked(
    command: list[str], *, cwd: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ReplayError(
            f"{' '.join(command)} failed with {result.returncode}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result


def exact_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key.lower() not in {"http_proxy", "https_proxy", "all_proxy"}
    }


def replay(
    frontier: Path, capsule: dict[str, Any], paths: dict[str, Path], source: Path
) -> dict[str, Any]:
    source_spec = capsule["source"]
    commit = source_spec["git_commit"]
    try:
        git_output(source, "cat-file", "-e", f"{commit}^{{commit}}")
    except ReplayError as error:
        raise ReplayError(
            f"prepared source checkout lacks frozen commit {commit}"
        ) from error
    require_equal(
        git_output(source, "rev-parse", f"{commit}^{{tree}}"),
        source_spec["git_tree"],
        "frozen source tree",
    )

    with tempfile.TemporaryDirectory(prefix="vela-formal-835-replay-") as temporary:
        worktree = Path(temporary) / "source"
        worktree.mkdir()
        extract_exact_source(source, worktree, commit)

        require_equal(
            sha256_bytes((worktree / "lean-toolchain").read_bytes()),
            capsule["environment"]["lean_toolchain_sha256"],
            "Lean toolchain root",
        )
        require_equal(
            sha256_bytes((worktree / "lake-manifest.json").read_bytes()),
            capsule["environment"]["lake_manifest_sha256"],
            "Lake manifest root",
        )
        packages = source / ".lake/packages"
        (worktree / ".lake").mkdir()
        (worktree / ".lake/packages").symlink_to(packages, target_is_directory=True)

        source_file = worktree / source_spec["path"]
        source_bytes = source_file.read_bytes()
        require_equal(
            sha256_bytes(source_bytes),
            source_spec["file_sha256"],
            "frozen source file root",
        )
        span = source_spec["declaration_span"].encode()
        require_equal(
            sha256_bytes(span),
            source_spec["declaration_span_sha256"],
            "declaration span root",
        )
        if source_bytes.count(span) != 1:
            raise ReplayError("frozen declaration span is not unique")

        proof_bytes = paths["proof"].read_bytes()
        marker = b"by\n  sorry\n"
        if marker not in span:
            raise ReplayError("frozen declaration span lacks the exact proof marker")
        statement_prefix = span[: span.index(marker)]
        replacement = statement_prefix + proof_bytes
        if not replacement.endswith(b"\n"):
            replacement += b"\n"
        verification_source = source_bytes.replace(span, replacement, 1)
        verification_source += (
            b"\n#print axioms Erdos835.property_iff_chromaticNumber\n"
        )
        require_equal(
            sha256_bytes(verification_source),
            capsule["expected"]["verification_source_sha256"],
            "generated verification-source root",
        )
        verification_path = worktree / "Verify835.lean"
        verification_path.write_bytes(verification_source)

        environment = exact_environment()
        build = network_denied_command(["lake", "build", "FormalConjecturesUtil"])
        run_checked(build, cwd=worktree, environment=environment)
        version = run_checked(
            network_denied_command(["lake", "env", "lean", "--version"]),
            cwd=worktree,
            environment=environment,
        ).stdout
        if f"version {capsule['environment']['lean_version']}" not in version:
            raise ReplayError(f"Lean version differs: {version.strip()}")

        lean = run_checked(
            network_denied_command(["lake", "env", "lean", "Verify835.lean"]),
            cwd=worktree,
            environment=environment,
        )
        combined_output = "\n".join(part for part in (lean.stdout, lean.stderr) if part)
        match = re.search(
            r"'Erdos835\.property_iff_chromaticNumber' depends on axioms: "
            r"\[([^]]*)\]",
            combined_output,
        )
        if not match:
            raise ReplayError("Lean output omitted the exact target axiom report")
        axioms = [item.strip() for item in match.group(1).split(",") if item.strip()]
        require_equal(axioms, capsule["expected"]["axioms"], "replayed axiom set")
        if "sorryAx" in axioms:
            raise ReplayError("replayed target depends on sorryAx")

    return {
        "schema": "formal-conjectures.lean-replay-result.v1",
        "ok": True,
        "authority_effect": "none",
        "standing_effect": "none",
        "proposal_id": capsule["identity"]["proposal_id"],
        "submission_id": capsule["identity"]["submission_id"],
        "claim_id": capsule["identity"]["claim_id"],
        "verification_record_id": capsule["identity"]["verification_record_id"],
        "source_commit": source_spec["git_commit"],
        "source_tree": source_spec["git_tree"],
        "proof_sha256": capsule["inputs"]["proof"]["sha256"],
        "verification_source_sha256": capsule["expected"][
            "verification_source_sha256"
        ],
        "lean_version": capsule["environment"]["lean_version"],
        "axioms": capsule["expected"]["axioms"],
        "sorryAx_present": False,
        "does_not_establish": capsule["limitations"],
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--frontier",
        type=Path,
        default=DEFAULT_FRONTIER,
        help="current Formal Conjectures Frontier checkout",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="prepared google-deepmind/formal-conjectures Git checkout",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate every retained binding without invoking Lean",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        frontier = arguments.frontier.resolve(strict=True)
        capsule, paths = validate_capsule(frontier)
        if arguments.validate_only:
            result = {
                "schema": "formal-conjectures.lean-replay-validation.v1",
                "ok": True,
                "authority_effect": "none",
                "standing_effect": "none",
                "proposal_id": capsule["identity"]["proposal_id"],
                "capsule_sha256": sha256_bytes(CAPSULE_PATH.read_bytes()),
            }
        else:
            source = prepared_source(arguments, frontier)
            result = replay(frontier, capsule, paths, source)
        sys.stdout.buffer.write(canonical_json_bytes(result))
        return 0
    except (OSError, ReplayError, subprocess.SubprocessError) as error:
        sys.stdout.buffer.write(
            canonical_json_bytes(
                {
                    "schema": "formal-conjectures.lean-replay-result.v1",
                    "ok": False,
                    "authority_effect": "none",
                    "standing_effect": "none",
                    "error": str(error),
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
