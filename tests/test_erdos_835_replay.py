from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "reproductions/erdos-835/capsule.json"
REPLAY = ROOT / "reproductions/erdos-835/replay.py"
PROOF = (
    ROOT
    / "records/artifacts/sha256"
    / "565309675bb0acbef3ad11b367c29f85eede2b1981d6f6395ca72f51c495b270"
)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class Erdos835ReplayCapsuleTests(unittest.TestCase):
    def test_capsule_validates_every_current_binding(self) -> None:
        result = subprocess.run(
            ["python3", str(REPLAY), "--frontier", str(ROOT), "--validate-only"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["ok"])
        self.assertEqual(output["authority_effect"], "none")
        self.assertEqual(output["standing_effect"], "none")
        self.assertEqual(output["proposal_id"], "vpr_08a91ee1b770f5cb")
        self.assertEqual(output["capsule_sha256"], sha256(CAPSULE))

    def test_capsule_is_evidence_only_and_binds_the_exact_proof(self) -> None:
        capsule = json.loads(CAPSULE.read_bytes())
        self.assertEqual(capsule["authority"], "evidence_only")
        self.assertEqual(capsule["standing_effect"], "none")
        self.assertEqual(
            capsule["inputs"]["proof"]["sha256"],
            "sha256:"
            "565309675bb0acbef3ad11b367c29f85eede2b1981d6f6395ca72f51c495b270",
        )
        self.assertEqual(capsule["inputs"]["proof"]["sha256"], sha256(PROOF))
        self.assertEqual(
            capsule["inputs"]["implementation"]["sha256"], sha256(REPLAY)
        )
        self.assertNotIn("decision", capsule["inputs"])
        self.assertIn(
            "only a separate authorized human Decision",
            capsule["limitations"][-1],
        )

    def test_mutated_proof_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="formal-replay-test-") as temporary:
            copy = Path(temporary) / "frontier"
            shutil.copytree(
                ROOT,
                copy,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            mutated = copy / PROOF.relative_to(ROOT)
            mutated.write_bytes(mutated.read_bytes() + b"\n-- mutation\n")
            result = subprocess.run(
                [
                    "python3",
                    str(REPLAY),
                    "--frontier",
                    str(copy),
                    "--validate-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertFalse(output["ok"])
        self.assertIn("root differs", output["error"])

    @unittest.skipUnless(
        os.environ.get("VELA_FORMAL_CONJECTURES_SOURCE"),
        "set VELA_FORMAL_CONJECTURES_SOURCE for the full Lean replay",
    )
    def test_full_lean_replay(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(REPLAY),
                "--frontier",
                str(ROOT),
                "--source",
                os.environ["VELA_FORMAL_CONJECTURES_SOURCE"],
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["ok"])
        self.assertEqual(
            output["axioms"], ["propext", "Classical.choice", "Quot.sound"]
        )
        self.assertFalse(output["sorryAx_present"])
        self.assertEqual(output["authority_effect"], "none")
        self.assertEqual(output["standing_effect"], "none")


if __name__ == "__main__":
    unittest.main()
