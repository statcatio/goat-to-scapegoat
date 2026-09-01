"""
Scrape full comment trees from the two World Cup final match threads.

Usage:
    pip install -r requirements.txt
    cp .env.example .env          # then fill in your Reddit app credentials
    python scrape.py              # writes data/*.json

Reddit read-only API access is fine for a "script" app with just client_id +
client_secret (no username/password needed) as long as we only read.
"""
import argparse
import json
import os
import time
from pathlib import Path

import praw
from dotenv import load_dotenv

load_dotenv()

# --- the two threads we're comparing -----------------------------------------
# (label, reddit submission id, human context)
THREADS = [
    {
        "label": "arg_fra_2022",
        "id": "zoz9vx",
        "match": "Argentina vs France",
        "event": "2022 World Cup Final (Qatar)",
    },
    {
        "label": "arg_spa_2026",
        "id": "1v0wji4",
        "match": "Spain vs Argentina",
        "event": "2026 World Cup Final",
    },
]

# Raw pulls land in data/raw/, which is gitignored. This repo is public and
# served by GitHub Pages, so a committed corpus would publish thousands of
# Reddit usernames and comment bodies as a downloadable file. The page only
# ever needs the aggregates that analyze.py derives from these.
RAW_DIR = Path(__file__).parent / "data" / "raw"
# replace_more(limit=None) fetches EVERY collapsed comment. For a final match
# thread that can be 10k+ comments and several minutes of API calls. Set an int
# (e.g. 32) for a faster partial pull while developing.
REPLACE_MORE_LIMIT = None


def get_reddit() -> praw.Reddit:
    missing = [
        k
        for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT")
        if not os.getenv(k)
    ]
    if missing:
        raise SystemExit(
            "Missing env vars: "
            + ", ".join(missing)
            + "\n-> copy .env.example to .env and fill it in "
            "(create a 'script' app at https://www.reddit.com/prefs/apps)."
        )
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
        check_for_async=False,
    )


def verify_threads(reddit: praw.Reddit) -> bool:
    """One API call per thread: confirm the ids resolve to what we expect."""
    ok = True
    for t in THREADS:
        try:
            sub = reddit.submission(id=t["id"])
            created = time.strftime("%Y-%m-%d", time.gmtime(sub.created_utc))
            print(f"  [{t['label']}] id={t['id']}")
            print(f"      title     : {sub.title!r}")
            print(f"      subreddit : r/{sub.subreddit.display_name}")
            print(f"      posted    : {created}")
            print(f"      comments  : {sub.num_comments}")
            print(f"      expected  : {t['match']} — {t['event']}")
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"  [{t['label']}] id={t['id']}  !! FAILED: {e}")
    return ok


def scrape_thread(reddit: praw.Reddit, thread: dict) -> dict:
    print(f"\n[{thread['label']}] fetching submission {thread['id']} ...")
    submission = reddit.submission(id=thread["id"])
    submission.comment_sort = "old"  # chronological -> good for the timeline

    print(f"  title: {submission.title!r}")
    print(f"  score: {submission.score}, comment count (reported): {submission.num_comments}")
    print("  expanding comment tree (this can take a few minutes)...")
    t0 = time.time()
    submission.comments.replace_more(limit=REPLACE_MORE_LIMIT)
    comments = submission.comments.list()
    print(f"  pulled {len(comments)} comments in {time.time() - t0:.0f}s")

    rows = []
    for c in comments:
        rows.append(
            {
                "id": c.id,
                "parent_id": c.parent_id,          # "t3_" = top-level (reply to post)
                "author": str(c.author) if c.author else "[deleted]",
                "body": c.body,
                "score": c.score,
                "created_utc": c.created_utc,       # unix seconds -> timeline x-axis
                "is_top_level": c.parent_id.startswith("t3_"),
                "is_submitter": bool(c.is_submitter),
            }
        )

    return {
        "meta": {
            "label": thread["label"],
            "match": thread["match"],
            "event": thread["event"],
            "submission_id": thread["id"],
            "title": submission.title,
            "score": submission.score,
            "num_comments_reported": submission.num_comments,
            "num_comments_pulled": len(rows),
            "created_utc": submission.created_utc,
            "scraped_at": time.time(),
        },
        "comments": rows,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true",
                    help="check the thread ids resolve, then stop (one call each)")
    ap.add_argument("--limit", type=int, default=None, metavar="N",
                    help="cap replace_more() at N for a fast partial pull while developing")
    args = ap.parse_args()

    reddit = get_reddit()
    print(f"read-only mode: {reddit.read_only}")

    if args.verify:
        print("\nverifying thread ids ...")
        raise SystemExit(0 if verify_threads(reddit) else 1)

    global REPLACE_MORE_LIMIT
    if args.limit is not None:
        REPLACE_MORE_LIMIT = args.limit
        print(f"partial pull: replace_more(limit={args.limit})")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for thread in THREADS:
        try:
            payload = scrape_thread(reddit, thread)
        except Exception as e:  # noqa: BLE001 - want to keep going to the next thread
            print(f"  !! failed on {thread['label']}: {e}")
            continue
        out = RAW_DIR / f"{thread['label']}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"  -> wrote {out} ({payload['meta']['num_comments_pulled']} comments)")


if __name__ == "__main__":
    main()
