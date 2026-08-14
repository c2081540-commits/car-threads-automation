import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

QUEUE_PATH = Path("data/content_queue.json")
PUBLISHED_PATH = Path("data/published.json")
OUTPUT_PATH = Path("SCHEDULE.md")
SLOT_LABELS = {"morning": "07:00", "noon": "12:00", "evening": "18:00"}
SLOT_ORDER = {"morning": 0, "noon": 1, "evening": 2}


def load_json(path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    queue = load_json(QUEUE_PATH, [])
    published = load_json(PUBLISHED_PATH, {})
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    rows = []
    for item in sorted(queue, key=lambda x: (x.get("date", ""), SLOT_ORDER.get(x.get("slot"), 99))):
        key = item.get("key", "")
        if key in published:
            state = "✅ 投稿済み"
        elif item.get("status") == "ready":
            state = "🟢 予約あり"
        elif item.get("status") == "disabled":
            state = "⏸ 無効"
        else:
            state = f"⚪ {item.get('status', '不明')}"
        image = "🖼 あり" if item.get("image_path") else "—"
        rows.append(
            f"| {item.get('date','')} | {SLOT_LABELS.get(item.get('slot'), item.get('slot',''))} | "
            f"{item.get('post_no','')} | {item.get('topic','')} | {image} | {state} |"
        )

    lines = [
        "# Threads 投稿スケジュール",
        "",
        "> `data/content_queue.json` と `data/published.json` から自動生成します。手動編集しないでください。",
        "",
        f"最終更新: {now.strftime('%Y-%m-%d %H:%M')} JST",
        "",
        "| 日付 | 時刻 | 投稿番号 | テーマ | 画像 | 状態 |",
        "|---|---:|---|---|---|---|",
        *rows,
        "",
        "## 表示",
        "",
        "- 🟢 予約あり: `status=ready` で今後の定時投稿対象",
        "- ✅ 投稿済み: `data/published.json` に公開記録あり",
        "- 🖼 あり: 投稿レコードに `image_path` あり",
        "- ⏸ 無効: 自動投稿対象外",
        "",
    ]
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
