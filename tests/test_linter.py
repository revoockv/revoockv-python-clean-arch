"""Unit tests of py_clean_arch_linter: rules, template configuration and severities."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import py_clean_arch_linter as linter  # noqa: E402
import templates  # noqa: E402

LAYOUT = {
    "data": ("data_sources", "models", "repositories"),
    "domain": ("entities", "repositories", "use_cases"),
    "presentation": ("di",),
}


class LinterTest(unittest.TestCase):
    def setUp(self) -> None:
        linter.configure(templates.resolve())
        self._tmp = tempfile.TemporaryDirectory()
        self.package = Path(self._tmp.name) / "src" / "app"
        (self.package / "features").mkdir(parents=True)
        (self.package / "di.py").write_text("register_notes(container)\n", encoding="utf-8")
        for layer, subs in LAYOUT.items():
            for sub in subs:
                (self.package / "features" / "notes" / layer / sub).mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()
        linter.configure(templates.resolve())

    def write(self, rel: str, code: str) -> Path:
        path = self.package / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(code), encoding="utf-8")
        return path

    def rules(self, path: Path, only: set[str] | None = None) -> list[str]:
        return [v.rule for v in linter.run(str(path), only or set(linter.RULES))]

    def test_module_constant_in_domain(self) -> None:
        path = self.write("features/notes/domain/entities/note.py", 'LIMIT = 3\n')
        self.assertIn("module_constants", self.rules(path))

    def test_class_constant_is_fine(self) -> None:
        path = self.write(
            "features/notes/domain/entities/note.py",
            '''
            """Note."""


            class Limits:
                """Limits."""

                MAX = 3
            ''',
        )
        self.assertEqual(self.rules(path, {"module_constants", "magic_numbers"}), [])

    def test_magic_string_in_use_case(self) -> None:
        path = self.write(
            "features/notes/domain/use_cases/add_note_use_case.py",
            '''
            class AddNoteUseCase:
                """Add."""

                async def __call__(self) -> str:
                    """Run."""
                    return "boom"
            ''',
        )
        self.assertIn("magic_strings", self.rules(path))

    def test_data_layer_is_not_checked_for_magic_strings(self) -> None:
        path = self.write("features/notes/data/models/note_model.py", 'def f() -> str:\n    return "id"\n')
        self.assertNotIn("magic_strings", self.rules(path))

    def test_use_case_without_call(self) -> None:
        path = self.write(
            "features/notes/domain/use_cases/add_note_use_case.py",
            'class AddNoteUseCase:\n    """Add."""\n\n    def run(self) -> None:\n        """Run."""\n',
        )
        self.assertIn("use_case_shape", self.rules(path))

    def test_domain_must_not_import_frameworks(self) -> None:
        path = self.write("features/notes/domain/entities/note.py", "import pydantic\n")
        self.assertIn("import_violation", self.rules(path))

    def test_file_size(self) -> None:
        body = "".join(f"X{i} = {i}\n" for i in range(linter.MAX_FILE_LINES + 1))
        path = self.write("features/notes/data/models/big_model.py", body)
        self.assertIn("file_size", self.rules(path, {"file_size"}))

    def test_configure_reads_params_and_warnings(self) -> None:
        class Fake:
            data = {
                "structure": {"required": LAYOUT, "optional": {"data": ["services"]}, "strict_layers": ["data"]},
                "lint": {"warn": ["file_size"], "params": {"max_file_lines": 5, "constant_layers": ["domain"]}},
            }

        linter.configure(Fake())
        self.assertEqual(linter.MAX_FILE_LINES, 5)
        self.assertEqual(linter.CONSTANT_LAYERS, ("domain",))
        path = self.write("features/notes/presentation/di/notes_di.py", "".join(f"x{i} = 1\n" for i in range(9)))
        violations = linter.run(str(path), {"file_size"})
        self.assertEqual([v.rule for v in violations], ["file_size"])
        self.assertTrue(violations[0].is_warning)


if __name__ == "__main__":
    unittest.main()
