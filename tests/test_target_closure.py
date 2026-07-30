from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_target_closure import (  # noqa: E402
    TargetClosureError,
    validate,
    validate_index,
)


class TargetClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._temporary = tempfile.TemporaryDirectory()
        self.frontier = pathlib.Path(self._temporary.name)
        closure = json.loads(
            (
                ROOT
                / "targets/closures/formal-retain-erdos-424-correction.json"
            ).read_text()
        )
        paths = {
            ".vela/repository.json",
            "targets.json",
            closure["completed_packet"]["path"],
            "targets/closures/formal-retain-erdos-424-correction.json",
            *(row["path"] for row in closure["evidence"]),
        }
        for relative in sorted(paths):
            source = ROOT / relative
            destination = self.frontier / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        subprocess.run(["git", "init", "-q", str(self.frontier)], check=True)
        subprocess.run(["git", "-C", str(self.frontier), "add", "."], check=True)

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def read(self, relative: str) -> dict:
        return json.loads((self.frontier / relative).read_text())

    def write(self, relative: str, value: dict) -> None:
        (self.frontier / relative).write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        )

    def test_exact_retention_closure_preserves_local_standing(self) -> None:
        result = validate(self.frontier)
        self.assertEqual(result["local_standing_effect"], "none")
        self.assertEqual(
            result["verification_root"],
            "sha256:4fe6e7d6dd361ec4ebe70cb9aba2d4570da27a0a4b10fe0f42f59cbf14b92200",
        )

    def test_completed_target_cannot_remain_exposed(self) -> None:
        validate_index(self.frontier)
        index = self.read("targets.json")
        index["targets"] = [
            {
                "id": "formal:retain-erdos-424-correction",
                "state": "open",
            }
        ]
        self.write("targets.json", index)
        with self.assertRaisesRegex(TargetClosureError, "remains exposed"):
            validate_index(self.frontier)

    def test_malformed_completion_contract_is_rejected(self) -> None:
        relative = "targets/closures/formal-retain-erdos-424-correction.json"
        closure = self.read(relative)
        closure["completion_contract"]["local_standing_effect"] = "accepted"
        self.write(relative, closure)
        with self.assertRaisesRegex(TargetClosureError, "completion-contract root"):
            validate(self.frontier)

    def test_untracked_archive_is_rejected(self) -> None:
        relative = (
            "records/artifacts/sha256/"
            "3a1f083e55ead5818b3dad5eca163155cab1f8d8905be2b61ab58e3823a2b26c"
        )
        subprocess.run(
            ["git", "-C", str(self.frontier), "rm", "--cached", "-q", "--", relative],
            check=True,
        )
        with self.assertRaisesRegex(TargetClosureError, "untracked"):
            validate(self.frontier)

    def test_verification_root_drift_is_rejected(self) -> None:
        relative = (
            "records/verifications/sha256/"
            "4fe6e7d6dd361ec4ebe70cb9aba2d4570da27a0a4b10fe0f42f59cbf14b92200.json"
        )
        path = self.frontier / relative
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(TargetClosureError, "root drift"):
            validate(self.frontier)


if __name__ == "__main__":
    unittest.main()
