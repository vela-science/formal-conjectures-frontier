from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "scripts" / "build_target_index.py"
PACKET = ROOT / "targets" / "formal-erdos-835-property-iff-chromatic-number.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("build_target_index", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TargetIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_candidate_is_exact_and_deterministic(self) -> None:
        first = self.generator.canonical_bytes(self.generator.candidate())
        second = self.generator.canonical_bytes(self.generator.candidate())
        self.assertEqual(first, second)
        value = json.loads(first)
        self.assertEqual(value["schema"], "vela.target-index-candidate.v1")
        self.assertEqual(value["frontier_id"], "vfr_97d7d25957384f80")
        self.assertEqual(
            value["source"]["input_paths"],
            sorted(value["source"]["input_paths"]),
        )
        self.assertNotIn(
            "targets/formal-erdos-835-property-iff-chromatic-number.json",
            value["source"]["input_paths"],
        )
        self.assertEqual(len(value["targets"]), 1)
        self.assertEqual(
            value["targets"][0]["id"],
            "formal:erdos-835-property-iff-chromatic-number",
        )
        self.assertEqual(value["targets"][0]["rank"], 1)

    def test_cli_output_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outputs = [
                pathlib.Path(directory) / "first.json",
                pathlib.Path(directory) / "second.json",
            ]
            for output in outputs:
                subprocess.run(
                    ["python3", str(GENERATOR), "--output", str(output)],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())

    def test_packet_binds_exact_statement_environment_and_budget(self) -> None:
        packet = json.loads(PACKET.read_text())
        self.generator.validate_packet(packet)
        self.assertEqual(
            self.generator.sha256_root(
                packet["source"]["declaration_span"].encode()
            ),
            "sha256:82ecd5e20d93c83d348f3b473e55375fca272b380fe9259f68e7796c3b0b09ff",
        )
        self.assertEqual(packet["environment"]["lean_version"], "4.27.0")
        self.assertEqual(
            packet["environment"]["mathlib_git_commit"],
            "a3a10db0e9d66acbebf76c5e6a135066525ac900",
        )
        self.assertEqual(
            packet["budget"],
            {
                "compute": "cpu_only",
                "network": "denied",
                "maximum_wall_time_seconds": 3600,
            },
        )

    def test_packet_excludes_answer_leaks_and_preserves_authority(self) -> None:
        packet = json.loads(PACKET.read_text())
        exclusions = "\n".join(packet["input_policy"]["excluded_answer_sources"])
        self.assertIn("golden-environment", exclusions)
        self.assertIn("candidate proofs", exclusions)
        self.assertIn("Live network", exclusions)
        self.assertEqual(
            packet["authority"],
            {
                "accepted_standing_effect": "none",
                "human_key_access": "forbidden",
                "producer_ceiling": "pending_review",
                "requires_human_decision": True,
                "verification_ceiling": "evidence_only",
            },
        )
        self.assertEqual(
            packet["verification"]["axioms"]["forbidden"],
            ["sorryAx"],
        )
        self.assertIn(
            "does not prove Erdos835.erdos_835",
            packet["limitations"][1],
        )

    def test_generator_rejects_semantic_tampering(self) -> None:
        packet = json.loads(PACKET.read_text())
        tampered = copy.deepcopy(packet)
        tampered["authority"]["requires_human_decision"] = False
        with self.assertRaisesRegex(ValueError, "authority ceiling differs"):
            self.generator.validate_packet(tampered)


if __name__ == "__main__":
    unittest.main()
