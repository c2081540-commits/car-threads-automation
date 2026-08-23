import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .settings import settings
from .threads_api import ThreadsAPI


METRICS = ("views", "likes", "replies", "reposts", "quotes", "shares")
KEY_PATTERN = re.compile(r"-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})-")


def _metric_value(payload, metric):
    for item in payload.get("data", []):
        if item.get("name") != metric:
            continue
        values = item.get("values") or []
        value = values[-1].get("value", 0) if values else item.get("value", 0)
        if isinstance(value, dict):
            value = sum(v for v in value.values() if isinstance(v, (int, float)))
        return value if isinstance(value, (int, float)) else 0
    return 0


def _scheduled_at(key):
    match = KEY_PATTERN.search(key)
    if not match:
        return "", ""
    year, month, day, hour, minute = match.groups()
    return f"{year}-{month}-{day}T{hour}:{minute}:00+09:00", f"{hour}:{minute}"


def collect_insights(output_dir="data/insights", api=None, published_path=None):
    published_path = Path(published_path or settings.published_log_path)
    published = json.loads(published_path.read_text(encoding="utf-8"))
    api = api or ThreadsAPI()
    identity = api.verify_identity()
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    successful_metrics = 0

    for key, record in published.items():
        media_id = str(record["media_id"])
        media_error = ""
        try:
            media = api.get_media(media_id)
        except RuntimeError as exc:
            media = {}
            media_error = str(exc)
        metrics = {}
        errors = {}
        for metric in METRICS:
            try:
                metrics[metric] = _metric_value(api.get_media_insight(media_id, metric), metric)
                successful_metrics += 1
            except RuntimeError as exc:
                metrics[metric] = None
                errors[metric] = str(exc)
        scheduled_at, slot = _scheduled_at(key)
        text = media.get("text") or ""
        rows.append(
            {
                "key": key,
                "post_no": record.get("post_no", ""),
                "media_id": media_id,
                "permalink": media.get("permalink") or record.get("permalink", ""),
                "scheduled_at": scheduled_at,
                "slot": slot,
                "published_at": media.get("timestamp", ""),
                "media_type": media.get("media_type", "UNKNOWN"),
                "title": next((line.strip() for line in text.splitlines() if line.strip()), ""),
                "text": text,
                "metrics": metrics,
                "media_error": media_error,
                "metric_errors": errors,
            }
        )

    if not successful_metrics:
        raise RuntimeError("インサイト指標を1件も取得できませんでした。アクセストークンのthreads_manage_insights権限を確認してください")

    document = {"collected_at": collected_at, "account": identity, "posts": rows}
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "latest.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fields = ["key", "post_no", "media_id", "permalink", "scheduled_at", "slot", "published_at", "media_type", "title", "media_error", *METRICS]
    with (output / "latest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{k: row.get(k, "") for k in fields}, **row["metrics"]})
    return {"status": "collected", "posts": len(rows), "successful_metrics": successful_metrics, "output": str(output)}
