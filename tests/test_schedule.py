import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ScheduleGeneratorTest(unittest.TestCase):
    def test_generator_marks_image_and_published(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_schedule.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data/content_queue.json").write_text(json.dumps([
                {"key":"x","date":"2026-08-14","slot":"morning","post_no":"CAR-X","topic":"test","status":"ready","image_path":"img.png"}
            ]), encoding="utf-8")
            (root / "data/published.json").write_text(json.dumps({"x":{"post_no":"CAR-X"}}), encoding="utf-8")
            subprocess.run([sys.executable, str(script)], cwd=root, check=True)
            text = (root / "SCHEDULE.md").read_text(encoding="utf-8")
            self.assertIn("07:00", text)
            self.assertIn("🖼 あり", text)
            self.assertIn("✅ 投稿済み", text)


if __name__ == "__main__":
    unittest.main()
