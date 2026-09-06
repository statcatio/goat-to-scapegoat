# From GOAT to Scapegoat

**Live → <https://statcatio.github.io/goat-to-scapegoat/>**
· [The Lab](https://statcatio.github.io/goat-to-scapegoat/lab/)
· [statcat](https://statcatio.github.io/)

A data-driven narrative about how online sentiment toward Argentina's national
team shifted between two World Cup finals — 2022, which they won and Messi was
crowned the undisputed GOAT, and 2026, which they lost to Spain.

One question, asked honestly: **did Argentina change, or did we?**

## The finding

Sentiment toward Argentina, mean of P(positive) − P(negative) over comments
naming them, in the 42 days after each final:

| audience | 2022 (won) | 2026 (lost) |
| --- | --- | --- |
| FOX | **+0.349** · 21% negative | **−0.278** · 57% negative |
| FIFA | **+0.421** · 16% negative | **−0.166** · 47% negative |

Argentina won the first final and lost the second, so a fall is exactly what the
result alone would predict. **That is why France is in this piece.** France lost
the 2022 final and still drew net-positive sentiment — +0.142 (FOX) and +0.206
(FIFA). Argentina lost in 2026 and went net-negative. Losing does not account
for the gap, and the gap appears in both audiences independently.

Every subject people raised moved negative for Argentina. The Messi
conversation both shrank and soured: from 30% of comments at +0.431 in 2022 to
15% at −0.249 in 2026.

## What's in here

This repo **is** the published site — GitHub Pages serves it, so a push to
`main` is a deploy.

| Path | What it is |
| --- | --- |
| `index.html` | The article. Self-contained: inlined D3, CSS, photos. |
| `lab/` | [The Lab](https://statcatio.github.io/goat-to-scapegoat/lab/) — five prototypes, kept as they were when set aside. |
| `scrape_youtube.py` | Collects public comments via the YouTube Data API. |
| `analyze.py` | Scores them and writes the publishable aggregates. |
| `data/public/aggregates.json` | Counts, means, and the keyword lists. No usernames, no comment text. |
| `PRODUCT.md` · `DESIGN.md` | Product framing and the visual system. |
| `scrape.py` | The abandoned Reddit scraper, kept as a record. See below. |

## Method

- **Source:** public comments on four YouTube videos — each final's highlights
  from two channels, so the comparison can be checked against a second audience
  rather than resting on one.
  - FOX: [`Mxkg3qLIPC8`](https://youtu.be/Mxkg3qLIPC8) (2022) · [`x-cpRHf4xd4`](https://youtu.be/x-cpRHf4xd4) (2026)
  - FIFA: [`zhEWqfP6V_w`](https://youtu.be/zhEWqfP6V_w) (2022) · [`6HaHNYjnghE`](https://youtu.be/6HaHNYjnghE) (2026)
- **Scope:** 45,016 comments collected, 28,051 scored — top-level only, within
  42 days of each video's publication. Replies are excluded because the API caps
  inline replies at 5 per thread, so they came back ~40% captured; mixing a
  complete sample with a partial one would bias the comparison. The 42-day
  window makes 2022 (which has years of comments) and 2026 (which has weeks)
  comparable over equal elapsed time.
- **Sentiment:** `cardiffnlp/twitter-xlm-roberta-base-sentiment`. Multilingual
  by necessity — a large share of comments are Spanish, and an English-only
  model scores them neutral, which would quietly delete Argentina's own
  supporters and manufacture a decline that isn't there.
- **Attribution:** teams and subjects matched by keyword. The lists are
  published inside `aggregates.json` so the work can be checked.

### Limits

- Different opponents. France's fanbase is not Spain's; the control is strong
  but not perfect.
- Sarcasm defeats sentiment models. It defeats this one too.
- A comment naming two teams is counted for both.
- Conduct and tactics rest on small samples (n = 48–99) and are labelled as
  such in the piece.
- ~75% of each video's reported comment count was retrieved, consistently
  across all four.

The piece measures **the discourse about** Argentina. It does not issue a
verdict on the team's conduct.

## Why not Reddit

The piece was designed around Reddit match threads, which are timestamped
*during* the match. Reddit closed self-service Data API access under the
[Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy),
which applies to Reddit data however it is obtained — including third-party
mirrors — and states that research using data collected outside the Reddit for
Researchers Program violates it. `scrape.py` is kept as the record of that
approach; it cannot be run.

The cost of moving to YouTube is real: comments arrive *after* the match rather
than during it, so the timeline measures hours since the highlights posted
rather than minutes on the match clock.

## Running it

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env          # add YOUTUBE_API_KEY
./.venv/bin/python scrape_youtube.py --search   # find candidate videos
./.venv/bin/python scrape_youtube.py --check    # verify ids, catch disabled comments
./.venv/bin/python scrape_youtube.py            # full pull, ~4 min
./.venv/bin/python analyze.py                   # score, ~12 min
./.venv/bin/python analyze.py --from-cache      # re-aggregate instantly
```

Get a key at [console.cloud.google.com](https://console.cloud.google.com):
create a project, enable **YouTube Data API v3**, then Credentials → API key.
Free, self-service; quota is 10,000 units/day and a full pull costs under 800.

Raw pulls land in `data/raw/`, which is gitignored. This repo is public and
Pages serves every file in it, so a committed corpus would publish tens of
thousands of usernames and comment bodies — including comments their authors
have since deleted. Only the de-identified aggregates ship.

## Deploying

No build step. `git push` and it's live in about a minute. `.nojekyll` keeps
files served verbatim.

---

© 2026 Chloe Zhang · [LinkedIn](https://www.linkedin.com/in/chloeyuxinzhang/)
