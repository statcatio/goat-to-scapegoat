# From GOAT to Scapegoat

**Live → <https://statcatio.github.io/goat-to-scapegoat/>**
· [The Lab](https://statcatio.github.io/goat-to-scapegoat/lab/)
· [statcat.io](https://statcatio.github.io/)

A data-driven narrative about how online sentiment toward Argentina's national
team shifted between two World Cup finals — 2022 (won; Messi crowned the
undisputed GOAT) and 2026 — using real Reddit match-thread reactions.

One question, asked honestly: **did Argentina change, or did we?**

> ⚠️ **Status: placeholder data.** The two Reddit threads are identified but not
> yet scraped. Every figure and quote currently on the page is illustrative and
> labeled `SAMPLE`. Nothing here is a finding yet.

## What's in here

This repo **is** the published site — GitHub Pages serves it directly, so a push
to `main` is a deploy.

| Path | What it is |
| --- | --- |
| `index.html` | The article. Self-contained: inlined D3, CSS, and photos. |
| `lab/` | [The Lab](https://statcatio.github.io/goat-to-scapegoat/lab/) — the five prototypes, kept as they were when set aside. |
| `landing.html` | Plate I — the first hero. Copy survived, layout didn't. |
| `aspect-flow.html` | Plate II — theme flow, click-driven. Set aside. |
| `scrolly-flow.html` | Plate III — theme flow, scroll-driven. **Shipped.** |
| `flow-d3.html` | Plate IV — theme flow rebuilt in D3. Set aside. |
| `timeline-d3.html` | Plate V — the two-final timeline. **Shipped.** |
| `scrape.py` | Reddit comment-tree scraper (PRAW). |
| `PRODUCT.md` | Product framing: audience, purpose, principles, caveats. |
| `DESIGN.md` | The visual system the article is built on. |
| `data/` | Scraped output, reference clips, and screenshots. |

## Method

- **Source:** Reddit match threads via the official API (PRAW). Anonymous
  scraping is hard-blocked with a 403, so authenticated access is required.
  - 2022 — Argentina vs France, `r/worldcup` thread `zoz9vx`
  - 2026 — Spain vs Argentina, `r/worldcup` thread `1v0wji4`
- **Analysis:** comment-level sentiment and toxicity, bucketed *per team* —
  sentiment toward Argentina vs. toward the opponent — by player and country
  keyword matching.
- **Known caveat:** satire subreddits (e.g. r/soccercirclejerk) break
  off-the-shelf sentiment models. Sources are kept separate rather than pooled
  into a single misleading average.

The piece measures **the discourse about** Argentina. It does not issue a
verdict on the team's conduct.

## Running the scraper

You only need this to refresh the data; the site itself needs no build step.

<details>
<summary>One-time Reddit API setup (~10 min)</summary>

1. Log in to Reddit and go to <https://www.reddit.com/prefs/apps>
2. Click **"are you a developer? create an app..."** at the bottom
3. Fill in:
   - **name:** `wc-hatewatch`
   - **type:** **`script`** ← important
   - **redirect uri:** `http://localhost:8080` (unused, but required)
4. **create app** — the **client id** is the string under "personal use script",
   and the **secret** is the `secret` field

</details>

```bash
cp .env.example .env    # paste in your client id + secret
pip install -r requirements.txt
python scrape.py
```

Writes `data/arg_fra_2022.json` and `data/arg_spa_2026.json` — full comment
trees with author, score, body, and `created_utc` (the timeline axis).

> A World Cup **final** thread holds 10k+ comments, so a full pull takes a few
> minutes. To iterate faster, set `REPLACE_MORE_LIMIT = 32` near the top of
> `scrape.py`.

## Deploying

There is no build step and no publish script. GitHub Pages serves this repo as-is:

```bash
git add -A && git commit -m "..." && git push
```

Live in about a minute at `statcatio.github.io/goat-to-scapegoat/`.
`.nojekyll` is present so files are served verbatim.

## Next up

- Scrape both threads and replace every `SAMPLE` figure with real values
- `analyze.py` — per-comment sentiment + toxicity, bucketed per team
- Wire the real series into the timeline in `index.html`

---

© 2026 Chloe Zhang · [LinkedIn](https://www.linkedin.com/in/chloeyuxinzhang/)
