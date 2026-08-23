import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SOURCE = Path("data/insights/latest.json")
OUTPUT = Path("reports/insights_latest.md")
REACTIONS = ("likes", "replies", "reposts", "quotes", "shares")


def number(value):
    return value if isinstance(value, (int, float)) else 0


def engagement(post):
    return sum(number(post["metrics"].get(name)) for name in REACTIONS)


def rate(post):
    views = number(post["metrics"].get("views"))
    return engagement(post) / views * 100 if views else 0


def aggregate(posts, field):
    groups = defaultdict(list)
    for post in posts:
        groups[post.get(field) or "不明"].append(post)
    return sorted(
        ((name, len(items), sum(number(x["metrics"].get("views")) for x in items) / len(items), sum(rate(x) for x in items) / len(items)) for name, items in groups.items()),
        key=lambda row: row[2],
        reverse=True,
    )


def main():
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    posts = document["posts"]
    available = [post for post in posts if isinstance(post["metrics"].get("views"), (int, float))]
    now = datetime.now(timezone.utc)
    for post in available:
        raw = post.get("published_at") or post.get("scheduled_at")
        try:
            post["age_hours"] = (now - datetime.fromisoformat(raw.replace("Z", "+00:00"))).total_seconds() / 3600
        except (TypeError, ValueError):
            post["age_hours"] = 0
    mature = [post for post in available if post["age_hours"] >= 24]
    ranked = sorted(mature or available, key=lambda post: number(post["metrics"].get("views")), reverse=True)
    efficient = sorted((post for post in mature if number(post["metrics"].get("views")) >= 10), key=rate, reverse=True)
    media_groups = defaultdict(list)
    for post in mature or available:
        label = "画像あり" if post.get("media_type") in {"IMAGE", "CAROUSEL_ALBUM"} else "テキスト"
        media_groups[label].append(post)

    lines = [
        "# Threadsインサイト分析（最新）",
        "",
        f"取得日時: {document['collected_at']} / 公開ログ: {len(posts)}投稿 / 指標取得成功: {len(available)}投稿 / 24時間以上経過: {len(mature)}投稿",
        "",
        "> 数値は取得時点の累計です。投稿時期が違うため、閲覧数だけの順位は古い投稿ほど有利です。反応率は（いいね＋返信＋再投稿＋引用＋シェア）÷閲覧数で算出しています。",
        "",
        "## 閲覧数 上位10件（24時間以上経過）",
        "",
        "|順位|投稿|時間|形式|閲覧|反応|反応率|冒頭|",
        "|---:|---|---|---|---:|---:|---:|---|",
    ]
    for index, post in enumerate(ranked[:10], 1):
        title = post["title"].replace("|", "｜")[:45]
        lines.append(f"|{index}|[{post['post_no']}]({post['permalink']})|{post['slot']}|{post['media_type']}|{number(post['metrics'].get('views')):,.0f}|{engagement(post):,.0f}|{rate(post):.2f}%|{title}|")

    lines += ["", "## 反応率 上位10件（閲覧10以上・24時間以上経過）", "", "|順位|投稿|閲覧|反応率|冒頭|", "|---:|---|---:|---:|---|"]
    for index, post in enumerate(efficient[:10], 1):
        title = post["title"].replace("|", "｜")[:55]
        lines.append(f"|{index}|[{post['post_no']}]({post['permalink']})|{number(post['metrics'].get('views')):,.0f}|{rate(post):.2f}%|{title}|")

    lines += ["", "## 投稿時間別（24時間以上経過）", "", "|時間|件数|平均閲覧|平均反応率|", "|---|---:|---:|---:|"]
    for name, count, views, avg_rate in aggregate(mature or posts, "slot"):
        lines.append(f"|{name}|{count}|{views:,.1f}|{avg_rate:.2f}%|")

    lines += ["", "## 画像有無（24時間以上経過）", "", "|形式|件数|平均閲覧|平均反応率|", "|---|---:|---:|---:|"]
    for name, items in sorted(media_groups.items()):
        avg_views = sum(number(x["metrics"].get("views")) for x in items) / len(items)
        avg_rate = sum(rate(x) for x in items) / len(items)
        lines.append(f"|{name}|{len(items)}|{avg_views:,.1f}|{avg_rate:.2f}%|")

    unavailable_posts = [post for post in posts if post not in available]
    if unavailable_posts:
        labels = ", ".join(post["post_no"] for post in unavailable_posts)
        lines += ["", f"取得不能で集計から除外: {labels}（{len(unavailable_posts)}投稿）"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
