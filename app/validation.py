import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from PIL import Image

SLOTS = {"morning": "0700", "noon": "1200", "evening": "2000"}
FORMATS = {"text", "image", "question", "comparison", "warning", "traffic"}
IMAGE_SIZE = (1200, 675)


def load_queue(path="data/content_queue.json"):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("content_queue.jsonの最上位は配列である必要があります")
    return value


def validate_queue(path="data/content_queue.json", require_images=True):
    queue = load_queue(path)
    errors = []
    keys, post_nos, slots = [], [], []
    for index, item in enumerate(queue, 1):
        label = item.get("post_no") or f"#{index}"
        required = {"account_id", "key", "post_no", "date", "slot", "status", "format", "topic", "title", "body"}
        missing = sorted(required - set(item))
        if missing:
            errors.append(f"{label}: 必須項目不足 {missing}")
            continue
        keys.append(item["key"]); post_nos.append(item["post_no"]); slots.append((item["date"], item["slot"]))
        if item["account_id"] != "car": errors.append(f"{label}: account_idはcarのみ")
        if not re.fullmatch(r"CAR-\d{3,}", item["post_no"]): errors.append(f"{label}: 投稿番号形式が不正")
        try: date.fromisoformat(item["date"])
        except ValueError: errors.append(f"{label}: dateがYYYY-MM-DDではありません")
        if item["slot"] not in SLOTS: errors.append(f"{label}: slotが不正")
        if item["status"] not in {"draft", "ready", "published", "disabled"}: errors.append(f"{label}: statusが不正")
        if item["format"] not in FORMATS: errors.append(f"{label}: formatが不正")
        if len(item["body"]) > 500: errors.append(f"{label}: 本文が500文字超")
        image_path = item.get("image_path")
        if item["format"] != "text" and not image_path: errors.append(f"{label}: 画像投稿にimage_pathがありません")
        if image_path:
            p = Path(image_path)
            if not str(p).startswith("generated/weeks/"): errors.append(f"{label}: image_pathは週フォルダ内にしてください")
            expected = f"{item['date'].replace('-', '')}_{SLOTS.get(item['slot'], '')}_{item['post_no']}"
            if not p.name.startswith(expected): errors.append(f"{label}: 日時・番号と画像名が不一致")
            if require_images and not p.is_file(): errors.append(f"{label}: 画像が存在しません")
            elif require_images:
                with Image.open(p) as image:
                    if image.size != IMAGE_SIZE: errors.append(f"{label}: 画像サイズは1200x675ではありません")
    for name, values in (("key", keys), ("post_no", post_nos), ("日時枠", slots)):
        dup = [v for v, n in Counter(values).items() if n > 1]
        if dup: errors.append(f"{name}が重複しています: {dup}")
    return {"passed": not errors, "post_count": len(queue), "errors": errors}
