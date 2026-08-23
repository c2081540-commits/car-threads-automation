import json
import tempfile
import unittest
from pathlib import Path

from app.validation import validate_queue


class ValidationTest(unittest.TestCase):
    def test_empty_queue_is_valid(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "queue.json"; path.write_text("[]", encoding="utf-8")
            self.assertTrue(validate_queue(path, require_images=False)["passed"])

    def test_duplicate_slot_is_rejected(self):
        item = {"account_id":"car","key":"a","post_no":"CAR-001","date":"2026-08-12","slot":"morning","status":"ready","format":"text","topic":"車","title":"題","body":"本文"}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "queue.json"; path.write_text(json.dumps([item, {**item,"key":"b","post_no":"CAR-002"}]), encoding="utf-8")
            self.assertFalse(validate_queue(path, require_images=False)["passed"])

    def test_poll_with_two_to_four_options_is_valid(self):
        item = {"account_id":"car","key":"a","post_no":"CAR-100","date":"2026-09-01","slot":"noon","status":"ready","format":"poll","topic":"車","title":"題","body":"質問","poll_options":["A","B","C","D"]}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "queue.json"; path.write_text(json.dumps([item]), encoding="utf-8")
            self.assertTrue(validate_queue(path, require_images=False)["passed"])

    def test_poll_requires_at_least_two_options(self):
        item = {"account_id":"car","key":"a","post_no":"CAR-100","date":"2026-09-01","slot":"noon","status":"ready","format":"poll","topic":"車","title":"題","body":"質問","poll_options":["A"]}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "queue.json"; path.write_text(json.dumps([item]), encoding="utf-8")
            self.assertFalse(validate_queue(path, require_images=False)["passed"])


if __name__ == "__main__": unittest.main()
