from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from training_control import no_trainable_surface_v1 as authority


def make_runtime_tree(root: Path) -> None:
    for name in authority.REQUIRED_RUNTIME_FILES:
        path = root / name
        path.write_text("# retained CO runtime\n", encoding="utf-8")


class NonTrainableAuthorityTests(unittest.TestCase):
    def test_live_repository_is_non_trainable_and_contains_both_runtime_sources(self) -> None:
        payload = authority.audit()
        self.assertTrue(payload["complete"], payload["unresolved"])
        self.assertEqual(payload["missing_required_runtime_files"], [])
        self.assertIn("Assembler.py", payload["retained_python_files"])
        self.assertIn("Simulator.py", payload["retained_python_files"])
        self.assertEqual(payload["training_findings"], [])

    def test_empty_or_partial_tree_cannot_receive_no_training_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(authority, "ROOT", root):
                payload = authority.audit()
            self.assertFalse(payload["complete"])
            self.assertTrue(any(
                row["type"] == "required_runtime_source_missing"
                for row in payload["unresolved"]
            ))
            self.assertTrue(any(
                row["type"] == "no_runtime_python_source_scanned"
                for row in payload["unresolved"]
            ))

    def test_each_required_runtime_file_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_runtime_tree(root)
            for name in authority.REQUIRED_RUNTIME_FILES:
                path = root / name
                original = path.read_bytes()
                path.unlink()
                try:
                    with self.subTest(missing=name), mock.patch.object(authority, "ROOT", root):
                        payload = authority.audit()
                    self.assertFalse(payload["complete"])
                    self.assertIn(name, payload["missing_required_runtime_files"])
                finally:
                    path.write_bytes(original)

    def test_injected_training_primitive_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_runtime_tree(root)
            (root / "trainer.py").write_text(
                "class X:\n"
                "    def fit(self, data): return data\n"
                "X().fit([1])\n",
                encoding="utf-8",
            )
            with mock.patch.object(authority, "ROOT", root):
                payload = authority.audit()
            self.assertFalse(payload["complete"])
            self.assertTrue(any(
                row["kind"] == "training_call" and row["symbol"] == "fit"
                for row in payload["training_findings"]
            ))

    def test_root_profile_does_not_apply_training_resume_to_audit_job(self) -> None:
        source = (Path(__file__).resolve().parent / "run_all_training.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        assignments = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "PROFILE"
        }
        profile = assignments["PROFILE"]
        self.assertFalse(profile["require_native_resume"])
        self.assertFalse(profile["require_exact_resume"])
        self.assertFalse(profile["require_workload_surface_accounting"])
        self.assertTrue(profile["require_all_retained_trainable_source_reachability"])
        self.assertEqual(profile["jobs"][0]["is_training_job"], False)


if __name__ == "__main__":
    unittest.main()
