"""
Score the scraped comments and emit publishable aggregates.

Reads  : data/raw/*.json          (local only, gitignored — usernames + bodies)
Writes : data/public/aggregates.json  (numbers only — safe to commit and serve)

Method, in short:
  * top-level comments only. Replies came back at ~40% of their claimed counts
    because the API caps inline replies at 5 per thread; mixing a complete
    sample with a partial one would bias the comparison.
  * a fixed window of N days from each video's publication, so 2022 (which has
    years of comments) is compared against the same elapsed time as 2026.
  * multilingual sentiment, because a large share of comments are Spanish and
    an English-only model would silently score them neutral — which would drop
    Argentina's own supporters and manufacture a decline that isn't there.
  * team attribution by keyword, so the list is auditable and publishable.
"""
import argparse
import json
import re
import statistics
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
PUBLIC = ROOT / "data" / "public"

MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
WINDOW_DAYS = 42

# --- team attribution ---------------------------------------------------------
# Deliberately transparent: this list is published with the piece. Accents are
# stripped before matching, so "Mbappe" catches "Mbappé".
TEAMS = {
    "argentina": [
        "argentina", "argentine", "argentinian", "albiceleste", "afa",
        "messi", "leo messi", "di maria", "dimaria", "martinez", "dibu",
        "otamendi", "de paul", "depaul", "enzo", "mac allister", "macallister",
        "julian alvarez", "lautaro", "paredes", "scaloni", "argentino",
    ],
    "france": [
        "france", "french", "les bleus", "mbappe", "griezmann", "giroud",
        "dembele", "tchouameni", "lloris", "deschamps", "francia", "hernandez",
    ],
    "spain": [
        "spain", "spanish", "espana", "la roja", "yamal", "lamine",
        "ferran torres", "ferran", "pedri", "gavi", "rodri", "cucurella",
        "morata", "unai simon", "de la fuente", "espanol", "spaniard",
    ],
}


# --- topic attribution --------------------------------------------------------
# Same transparent approach as TEAMS: a published keyword list, matched on the
# accent-stripped text. Spanish terms are included because a large share of the
# comments are Spanish and an English-only list would under-count exactly the
# audience most invested in Argentina.
TOPICS = {
    "refereeing": [
        "ref", "refs", "referee", "reff", "var", "penalty", "penalties", "pen",
        "offside", "handball", "foul", "rigged", "robbed", "cheat", "cheated",
        "cheating", "biased", "bias", "corrupt", "fix", "fixed", "arbitro",
        "penal", "robaron", "robo", "tramposo", "tramposos", "corrupto",
    ],
    "conduct": [
        "disrespect", "disrespectful", "arrogant", "arrogance", "classless",
        "humble", "humility", "respect", "taunt", "taunting", "mock", "mocking",
        "gloat", "gloating", "provoke", "provoking", "trash talk", "bobo",
        "celebration", "celebrate", "celebrating", "sportsmanship", "toxic",
        "humilde", "arrogante", "irrespetuoso", "falta de respeto", "burla",
    ],
    "messi": [
        "messi", "leo", "goat", "greatest", "best player", "el diez", "la pulga",
        "maradona", "legend", "got", "d10s",
    ],
    "tactics": [
        "tactics", "tactical", "formation", "midfield", "defense", "defence",
        "possession", "press", "pressing", "coach", "manager", "scaloni",
        "substitution", "sub", "lineup", "counter", "tactica", "entrenador",
        "formacion", "mediocampo", "defensa",
    ],
    "crowd": [
        "fans", "fan", "crowd", "boo", "booed", "booing", "whistle", "whistled",
        "stadium", "supporters", "atmosphere", "hooligan", "chant", "chanting",
        "aficionados", "hinchada", "silbar", "silbaron", "abuchear", "publico",
    ],
}

ACCENTS = str.maketrans("áàâäãéèêëíìîïóòôöõúùûüñçÁÀÂÄÃÉÈÊËÍÌÎÏÓÒÔÖÕÚÙÛÜÑÇ",
                        "aaaaaeeeeiiiiooooouuuuncAAAAAEEEEIIIIOOOOOUUUUNC")
URL = re.compile(r"https?://\S+|www\.\S+")
WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    t = URL.sub(" ", text or "").translate(ACCENTS).lower()
    return WS.sub(" ", t).strip()


def _match(norm: str, groups: dict) -> list:
    return [name for name, words in groups.items()
            if any(re.search(rf"\b{re.escape(w)}\b", norm) for w in words)]


def attribute(norm: str) -> list:
    """Which teams does this comment talk about? May be none or several."""
    return _match(norm, TEAMS)


def topics_of(norm: str) -> list:
    """Which subjects does it raise? May be none or several."""
    return _match(norm, TOPICS)


def load(label: str) -> tuple:
    d = json.loads((RAW / f"{label}.json").read_text())
    pub = datetime.fromisoformat(d["meta"]["published_at"].replace("Z", "+00:00"))
    cutoff = pub + timedelta(days=WINDOW_DAYS)
    rows = []
    for c in d["comments"]:
        if c["is_reply"] or not c.get("published_at"):
            continue
        ts = datetime.fromisoformat(c["published_at"].replace("Z", "+00:00"))
        if not (pub <= ts <= cutoff):
            continue
        body = (c.get("body") or "").strip()
        if len(body) < 3:
            continue
        rows.append({"ts": ts,
                     "day": (ts - pub).days,
                     "hour": int((ts - pub).total_seconds() // 3600),
                     "body": body,
                     "likes": c.get("likes", 0)})
    return d["meta"], pub, rows


def score_all(texts: list, batch: int) -> list:
    """Signed sentiment in [-1, 1]: P(positive) - P(negative)."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    print(f"  loading {MODEL} (first run downloads ~1.1GB) ...")
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    model.eval()

    order = {v.lower(): k for k, v in model.config.id2label.items()}
    neg, pos = order.get("negative", 0), order.get("positive", 2)

    out, t0 = [], time.time()
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            chunk = texts[i:i + batch]
            enc = tok(chunk, padding=True, truncation=True, max_length=128,
                      return_tensors="pt")
            probs = torch.softmax(model(**enc).logits, dim=-1)
            out.extend((probs[:, pos] - probs[:, neg]).tolist())
            done = min(i + batch, len(texts))
            rate = done / max(time.time() - t0, 1e-6)
            eta = (len(texts) - done) / max(rate, 1e-6)
            print(f"\r  scored {done:,}/{len(texts):,}  ({rate:.0f}/s, eta {eta/60:.1f}m)",
                  end="", flush=True)
    print()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--sample", type=int, default=None,
                    help="score only the first N per dataset (quick dry run)")
    ap.add_argument("--from-cache", action="store_true",
                    help="reuse data/raw/scored.json instead of re-running the model")
    args = ap.parse_args()

    labels = ["fox_arg_fra_2022", "fox_arg_spa_2026",
              "fifa_arg_fra_2022", "fifa_arg_spa_2026"]

    datasets = {}
    for lab in labels:
        meta, pub, rows = load(lab)
        if args.sample:
            rows = rows[:args.sample]
        for r in rows:
            n = normalize(r["body"])
            r["teams"] = attribute(n)
            r["topics"] = topics_of(n)
        datasets[lab] = {"meta": meta, "pub": pub, "rows": rows}
        print(f"{lab:<20} {len(rows):>7,} top-level comments in first {WINDOW_DAYS}d")

    cache = RAW / "scored.json"
    if args.from_cache and cache.exists():
        print(f"\nreusing cached scores from {cache}")
        cached = json.loads(cache.read_text())
        for lab, d in datasets.items():
            got = cached.get(lab, [])
            if len(got) != len(d["rows"]):
                raise SystemExit(f"cache mismatch for {lab}: {len(got)} vs {len(d['rows'])}"
                                 " — rerun without --from-cache")
            for r, sc in zip(d["rows"], got):
                r["s"] = sc
    else:
        all_texts = [r["body"] for d in datasets.values() for r in d["rows"]]
        print(f"\nscoring {len(all_texts):,} comments")
        scores = score_all(all_texts, args.batch)
        it = iter(scores)
        for d in datasets.values():
            for r in d["rows"]:
                r["s"] = next(it)
        cache.write_text(json.dumps(
            {lab: [r["s"] for r in d["rows"]] for lab, d in datasets.items()}))
        print(f"  cached scores -> {cache} (rerun with --from-cache to skip the model)")

    # --- aggregate ------------------------------------------------------------
    out = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "method": {
            "source": "YouTube Data API v3, public comments",
            "model": MODEL,
            "sentiment": "P(positive) - P(negative), range -1 to +1",
            "scope": "top-level comments only; replies excluded (API caps inline "
                     "replies at 5/thread, so replies were ~40% captured)",
            "window_days": WINDOW_DAYS,
            "window_note": "measured from each video's publication date, so both "
                           "finals are compared over equal elapsed time",
            "attribution": "keyword match on team/player names, accent-insensitive",
            "keywords": TEAMS,
            "topic_keywords": TOPICS,
            "topic_note": "share is the percentage of scored comments in the window "
                          "mentioning that topic; a comment can raise several",
        },
        "datasets": {},
    }

    for lab, d in datasets.items():
        rows, meta = d["rows"], d["meta"]
        by_team = {}
        for team in TEAMS:
            sel = [r for r in rows if team in r["teams"]]
            if sel:
                ss = [r["s"] for r in sel]
                by_team[team] = {
                    "n": len(sel),
                    "mean": round(statistics.fmean(ss), 4),
                    "median": round(statistics.median(ss), 4),
                    "pct_negative": round(sum(1 for x in ss if x < -0.25) / len(ss) * 100, 1),
                    "pct_positive": round(sum(1 for x in ss if x > 0.25) / len(ss) * 100, 1),
                }
        daily = defaultdict(list)
        for r in rows:
            daily[r["day"]].append(r["s"])

        def series(bucket_key, keep, team=None):
            b = defaultdict(list)
            for r in rows:
                if r[bucket_key] > keep:
                    continue
                if team is None or team in r["teams"]:
                    b[r[bucket_key]].append(r["s"])
            return [{"t": k, "n": len(v), "mean": round(statistics.fmean(v), 4)}
                    for k, v in sorted(b.items()) if len(v) >= 5]

        by_topic = {}
        for topic in TOPICS:
            sel = [r for r in rows if topic in r["topics"]]
            if len(sel) >= 20:
                ss = [r["s"] for r in sel]
                arg = [r["s"] for r in sel if "argentina" in r["teams"]]
                by_topic[topic] = {
                    "n": len(sel),
                    "share": round(len(sel) / len(rows) * 100, 1),
                    "mean": round(statistics.fmean(ss), 4),
                    "pct_negative": round(sum(1 for x in ss if x < -0.25) / len(ss) * 100, 1),
                    "n_argentina": len(arg),
                    "mean_argentina": round(statistics.fmean(arg), 4) if len(arg) >= 20 else None,
                }

        by_day_team = {t: series("day", WINDOW_DAYS - 1, t) for t in TEAMS}
        by_hour_team = {t: series("hour", 47, t) for t in TEAMS}
        by_hour_all = series("hour", 47)
        alls = [r["s"] for r in rows]
        out["datasets"][lab] = {
            "video_id": meta["video_id"],
            "channel": meta["channel"],
            "title": meta["title"],
            "published_at": meta["published_at"],
            "match": meta["match"],
            "event": meta["event"],
            "n_scored": len(rows),
            "overall": {
                "mean": round(statistics.fmean(alls), 4),
                "pct_negative": round(sum(1 for x in alls if x < -0.25) / len(alls) * 100, 1),
                "pct_positive": round(sum(1 for x in alls if x > 0.25) / len(alls) * 100, 1),
            },
            "by_team": by_team,
            "by_topic": by_topic,
            "by_day": [{"day": k, "n": len(v), "mean": round(statistics.fmean(v), 4)}
                       for k, v in sorted(daily.items())],
            "by_day_team": by_day_team,
            "by_hour": by_hour_all,
            "by_hour_team": by_hour_team,
            "unattributed": sum(1 for r in rows if not r["teams"]),
        }

    PUBLIC.mkdir(parents=True, exist_ok=True)
    dest = PUBLIC / "aggregates.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n-> {dest}")

    # --- the comparison the piece rests on ------------------------------------
    print("\n" + "=" * 72)
    print("SENTIMENT TOWARD EACH TEAM  (mean, -1..+1)")
    print("=" * 72)
    for pair in ("fox", "fifa"):
        print(f"\n{pair.upper()}")
        for lab in [l for l in labels if l.startswith(pair)]:
            ds = out["datasets"][lab]
            year = "2022" if "2022" in lab else "2026"
            bits = "  ".join(
                f"{t}={v['mean']:+.3f} (n={v['n']:,}, {v['pct_negative']:.0f}% neg)"
                for t, v in ds["by_team"].items())
            print(f"  {year}  overall={ds['overall']['mean']:+.3f}   {bits}")
    print("\nThe control: Argentina WON 2022 and LOST 2026, so compare like with like —")
    print("France (loser, 2022) against Argentina (loser, 2026).")

    print("\n" + "=" * 72)
    print("TOPICS  (share of comments, and sentiment where Argentina is named)")
    print("=" * 72)
    for pair in ("fox", "fifa"):
        a = out["datasets"][f"{pair}_arg_fra_2022"]["by_topic"]
        b = out["datasets"][f"{pair}_arg_spa_2026"]["by_topic"]
        print(f"\n{pair.upper()}   {'topic':<12} {'share 22':>9} {'share 26':>9} "
              f"{'arg 22':>8} {'arg 26':>8}")
        for t in TOPICS:
            if t in a and t in b:
                m22 = a[t]["mean_argentina"]; m26 = b[t]["mean_argentina"]
                f22 = f"{m22:+.3f}" if m22 is not None else "  n/a"
                f26 = f"{m26:+.3f}" if m26 is not None else "  n/a"
                print(f"       {t:<12} {a[t]['share']:>8.1f}% {b[t]['share']:>8.1f}% "
                      f"{f22:>8} {f26:>8}")


if __name__ == "__main__":
    main()
