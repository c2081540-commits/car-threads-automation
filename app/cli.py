import argparse
import json
from pathlib import Path
from urllib.parse import quote

from .settings import settings
from .threads_api import ThreadsAPI
from .validation import load_queue, validate_queue
from .insights import collect_insights


def show(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _published():
    path = Path(settings.published_log_path)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _save_published(value):
    path = Path(settings.published_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def select(slot, target_date):
    matches = [x for x in load_queue(settings.content_queue_path) if x.get("date") == target_date and x.get("slot") == slot and x.get("status") == "ready"]
    if len(matches) > 1: raise RuntimeError(f"{target_date} {slot}に複数の予約があります")
    return matches[0] if matches else None


def dispatch(slot, target_date):
    item = select(slot, target_date)
    if not item: return {"status": "no_content", "date": target_date, "slot": slot}
    done = _published()
    if item["key"] in done: raise RuntimeError("この投稿は公開済みです。再送しません")
    if not settings.auto_publish: return {"status": "preview_only", "post_no": item["post_no"]}
    api = ThreadsAPI(); api.verify_identity()
    image_path = item.get("image_path")
    if image_path:
        if not settings.image_base_url: raise RuntimeError("IMAGE_BASE_URLが未設定です")
        url = settings.image_base_url.rstrip("/") + "/" + quote(image_path)
        media_id = api.publish_image(item["body"], url, topic_tag=item.get("topic_tag"))
    else:
        media_id = api.publish_text(item["body"], topic_tag=item.get("topic_tag"))
    media = api.wait_until_published(media_id)
    reply_ids = []
    for reply in item.get("replies", []):
        reply_id = api.publish_text(reply["text"], media_id)
        api.wait_until_published(reply_id); reply_ids.append(reply_id)
    done[item["key"]] = {"post_no": item["post_no"], "media_id": media_id, "permalink": media["permalink"], "reply_ids": reply_ids}
    _save_published(done)
    return {"status": "published", **done[item["key"]]}


def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate"); sub.add_parser("verify-auth"); sub.add_parser("collect-insights")
    p = sub.add_parser("dispatch"); p.add_argument("slot", choices=("morning", "noon", "evening")); p.add_argument("--date", required=True); p.add_argument("--require-content", action="store_true")
    args = parser.parse_args()
    if args.cmd == "validate":
        result = validate_queue(settings.content_queue_path)
        show(result)
        if not result["passed"]: raise SystemExit(1)
    elif args.cmd == "verify-auth": show(ThreadsAPI().verify_identity())
    elif args.cmd == "collect-insights": show(collect_insights())
    else:
        result = dispatch(args.slot, args.date)
        show(result)
        if args.require_content and result.get("status") == "no_content":
            raise SystemExit(1)


if __name__ == "__main__": main()
