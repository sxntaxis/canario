from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_esparza_shadow import (
    SOURCE_KIND,
    SOURCE_NAME,
    _selected_sections,
    assert_source_binding_continuity,
    load_or_create_source_binding,
)


class EsparzaShadowRunnerTests(unittest.TestCase):
    def test_source_binding_is_stable_across_runs(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "source-binding.json"
            first = load_or_create_source_binding(path)
            second = load_or_create_source_binding(path)
            self.assertEqual(first, second)
            self.assertEqual(first.kind, SOURCE_KIND)
            self.assertEqual(first.name, SOURCE_NAME)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_binding_tamper_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "source-binding.json"
            source = load_or_create_source_binding(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["source"]["name"] = "Different source"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                load_or_create_source_binding(path)
            self.assertTrue(source.id.startswith("src_"))

    def test_existing_database_without_source_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "actakit.sqlite3"
            binding = root / "source-binding.json"
            db.write_bytes(b"placeholder")
            with self.assertRaisesRegex(RuntimeError, "source-binding.json is missing"):
                assert_source_binding_continuity(db, binding)

    def test_section_filter_preserves_default_order_and_rejects_unknown(self):
        sections = _selected_sections(["junta_vial", "concejo"])
        self.assertEqual([section.key for section in sections], ["concejo", "junta_vial"])
        with self.assertRaisesRegex(ValueError, "unknown Esparza sections"):
            _selected_sections(["invented"])


if __name__ == "__main__":
    unittest.main()
