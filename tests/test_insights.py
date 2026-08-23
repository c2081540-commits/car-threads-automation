import json
import tempfile
import unittest
from pathlib import Path
from app.insights import _metric_value, _scheduled_at, collect_insights


class FakeAPI:
    def verify_identity(self): return {"id": "1", "username": "test"}
    def get_media(self, media_id): return {"id": media_id, "text": "見出し\n本文", "timestamp": "2026-08-20T03:00:00+0000", "media_type": "TEXT", "permalink": "https://example.test/post"}
    def get_media_insight(self, media_id, metric): return {"data": [{"name": metric, "values": [{"value": 12}]}]}


class InsightsTest(unittest.TestCase):
    def test_metric_value(self):
        self.assertEqual(_metric_value({"data": [{"name": "views", "values": [{"value": 9}]}]}, "views"), 9)

    def test_schedule_key(self):
        self.assertEqual(_scheduled_at("car-20260821-1200-044"), ("2026-08-21T12:00:00+09:00", "12:00"))

    def test_collect_writes_json_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            published = root / "published.json"
            published.write_text(json.dumps({"car-20260821-1200-044": {"post_no": "CAR-044", "media_id": "99", "permalink": "x"}}), encoding="utf-8")
            result = collect_insights(root / "out", api=FakeAPI(), published_path=published)
            self.assertEqual(result["posts"], 1)
            self.assertTrue((root / "out/latest.json").is_file())
            self.assertTrue((root / "out/latest.csv").is_file())


if __name__ == "__main__": unittest.main()
