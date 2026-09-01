"""
Pull public comments on the two World Cup final videos from the YouTube Data API.

Why YouTube and not Reddit: Reddit closed self-service Data API access under the
Responsible Builder Policy, and that policy applies to Reddit data however it is
obtained — including third-party mirrors. The YouTube Data API is self-service,
free, and its terms permit reading public comments.

What changes because of it: YouTube comments are posted *after* the match, not
during it, so the timeline axis is "days since the final" rather than "minute of
the match".

Usage:
    ./.venv/bin/python scrape_youtube.py --search           # find candidate videos
    ./.venv/bin/python scrape_youtube.py --check            # confirm the chosen ids
    ./.venv/bin/python scrape_youtube.py --limit 500        # small test pull
    ./.venv/bin/python scrape_youtube.py                    # full pull
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://www.googleapis.com/youtube/v3"

# Fill video_id in once --search shows you the right videos.
VIDEOS = [
    {
        "label": "arg_fra_2022",
        "video_id": None,
        "match": "Argentina vs France",
        "event": "2022 World Cup Final (Qatar)",
        "search": "Argentina France 2022 World Cup final highlights",
    },
    {
        "label": "arg_spa_2026",
        "video_id": None,
        "match": "Spain vs Argentina",
        "event": "2026 World Cup Final",
        "search": "Spain Argentina 2026 World Cup final highlights",
    },
]

RAW_DIR = Path(__file__).parent / "data" / "raw"

# quota: search.list = 100 units, videos.list = 1, commentThreads.list = 1 per
# page of 100. Default daily quota is 10,000, so a full pull is cheap.
PAGE = 100
SLEEP = 0.1


def key() -> str:
    k = os.getenv("YOUTUBE_API_KEY")
    if not k or k == "your_api_key_here":
        raise SystemExit(
            "YOUTUBE_API_KEY is not set.\n"
            "-> console.cloud.google.com: create a project, enable 'YouTube Data API v3',\n"
            "   Credentials -> Create credentials -> API key, then put it in .env"
        )
    return k


def call(endpoint: str, **params) -> dict:
    params["key"] = key()
    r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
    if r.status_code != 200:
        try:
            err = r.json()["error"]
            reason = err["errors"][0].get("reason", "")
            raise SystemExit(f"API error {r.status_code} ({reason}): {err.get('message')}")
        except (KeyError, ValueError):
            raise SystemExit(f"API error {r.status_code}: {r.text[:300]}")
    return r.json()


def describe(video_ids: list) -> list:
    """videos.list -> title, channel, date, view/comment counts."""
    out = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        d = call("videos", part="snippet,statistics", id=",".join(chunk))
        for it in d.get("items", []):
            s, st = it["snippet"], it.get("statistics", {})
            out.append(
                {
                    "video_id": it["id"],
                    "title": s["title"],
                    "channel": s["channelTitle"],
                    "published_at": s["publishedAt"],
                    "views": int(st.get("viewCount", 0)),
                    "comments": int(st["commentCount"]) if "commentCount" in st else None,
                }
            )
    return out


def do_search() -> None:
    for v in VIDEOS:
        print(f"\n=== {v['label']}: {v['match']} — {v['event']} ===")
        print(f"    query: {v['search']!r}")
        d = call("search", part="snippet", q=v["search"], type="video",
                 maxResults=15, order="relevance")
        ids = [it["id"]["videoId"] for it in d.get("items", [])]
        if not ids:
            print("    no results")
            continue
        rows = describe(ids)
        rows.sort(key=lambda r: (r["comments"] or 0), reverse=True)
        print(f"    {'comments':>9}  {'views':>12}  {'published':<11} channel / title")
        for r in rows:
            c = "disabled" if r["comments"] is None else f"{r['comments']:,}"
            print(f"    {c:>9}  {r['views']:>12,}  {r['published_at'][:10]:<11} "
                  f"{r['channel'][:22]} / {r['title'][:58]}")
        print("    -> put the chosen id in VIDEOS[...]['video_id'] in this file")


def do_check() -> bool:
    ids = [v["video_id"] for v in VIDEOS if v["video_id"]]
    if len(ids) != len(VIDEOS):
        missing = [v["label"] for v in VIDEOS if not v["video_id"]]
        print(f"!! video_id not set for: {', '.join(missing)}")
        print("   run --search first, then edit VIDEOS in this file.")
        return False
    ok = True
    for v, r in zip(VIDEOS, describe(ids)):
        c = "DISABLED" if r["comments"] is None else f"{r['comments']:,}"
        print(f"  [{v['label']}] {r['video_id']}")
        print(f"      title    : {r['title']}")
        print(f"      channel  : {r['channel']}")
        print(f"      published: {r['published_at'][:10]}")
        print(f"      comments : {c}   views: {r['views']:,}")
        print(f"      expected : {v['match']} — {v['event']}")
        if r["comments"] is None:
            ok = False
            print("      !! comments are disabled on this video — pick another")
    return ok


def pull(video: dict, cap: int | None) -> dict:
    vid = video["video_id"]
    print(f"\n[{video['label']}] pulling comments for {vid} ...")
    rows, token, pages, t0 = [], None, 0, time.time()
    while True:
        params = dict(part="snippet,replies", videoId=vid, maxResults=PAGE, order="time",
                      textFormat="plainText")
        if token:
            params["pageToken"] = token
        d = call("commentThreads", **params)
        for it in d.get("items", []):
            top = it["snippet"]["topLevelComment"]["snippet"]
            rows.append({
                "id": it["id"],
                "parent_id": None,
                "author": top.get("authorDisplayName"),
                "body": top.get("textOriginal", ""),
                "likes": top.get("likeCount", 0),
                "published_at": top.get("publishedAt"),
                "is_reply": False,
                "reply_count": it["snippet"].get("totalReplyCount", 0),
            })
            for rep in it.get("replies", {}).get("comments", []):
                rs = rep["snippet"]
                rows.append({
                    "id": rep["id"],
                    "parent_id": it["id"],
                    "author": rs.get("authorDisplayName"),
                    "body": rs.get("textOriginal", ""),
                    "likes": rs.get("likeCount", 0),
                    "published_at": rs.get("publishedAt"),
                    "is_reply": True,
                    "reply_count": 0,
                })
        pages += 1
        print(f"\r  page {pages}: {len(rows):,} comments", end="", flush=True)
        token = d.get("nextPageToken")
        if not token or (cap and len(rows) >= cap):
            break
        time.sleep(SLEEP)
    print(f"\n  done: {len(rows):,} comments in {time.time() - t0:.0f}s ({pages} pages)")

    meta = describe([vid])[0]
    return {
        "meta": {
            "source": "youtube-data-api-v3",
            "label": video["label"],
            "match": video["match"],
            "event": video["event"],
            "video_id": vid,
            "title": meta["title"],
            "channel": meta["channel"],
            "published_at": meta["published_at"],
            "views": meta["views"],
            "comments_reported": meta["comments"],
            "comments_pulled": len(rows),
            "scraped_at": time.time(),
        },
        "comments": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--search", action="store_true", help="find candidate videos and stop")
    ap.add_argument("--check", action="store_true", help="verify the chosen video ids and stop")
    ap.add_argument("--limit", type=int, default=None, metavar="N",
                    help="stop after roughly N comments per video (test pulls)")
    args = ap.parse_args()

    if args.search:
        do_search()
        return
    if args.check:
        raise SystemExit(0 if do_check() else 1)
    if not do_check():
        raise SystemExit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for v in VIDEOS:
        try:
            payload = pull(v, args.limit)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"  !! failed on {v['label']}: {e}", file=sys.stderr)
            continue
        out = RAW_DIR / f"{v['label']}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"  -> {out}  ({payload['meta']['comments_pulled']:,} comments)")


if __name__ == "__main__":
    main()
