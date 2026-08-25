# WC Hate-Watch — Argentina sentiment, 2022 vs 2026

Compare Reddit sentiment toward each team across two World Cup finals:

- **2022** — Argentina vs France (`r/worldcup`, thread `zoz9vx`)
- **2026** — Spain vs Argentina (`r/worldcup`, thread `1v0wji4`)

## Setup (~10 min, one time)

### 1. Create a free Reddit "script" app
1. Log in to Reddit, go to <https://www.reddit.com/prefs/apps>
2. Click **"are you a developer? create an app..."** (bottom of page)
3. Fill in:
   - **name:** `wc-hatewatch`
   - **type:** select **`script`** ← important
   - **redirect uri:** `http://localhost:8080` (unused, but required)
4. Click **create app**. You'll now see:
   - the **client id** = the string just under "personal use script"
   - the **secret** = the `secret` field

### 2. Add credentials
```bash
cp .env.example .env
# edit .env and paste in your client id + secret
```

### 3. Install + run
```bash
pip install -r requirements.txt
python scrape.py
```

This writes `data/arg_fra_2022.json` and `data/arg_spa_2026.json` — full comment
trees with author, score, body, and `created_utc` timestamps (the timeline axis).

> A World Cup **final** match thread can hold 10k+ comments, so the full pull may
> take a few minutes. To iterate faster while developing, set
> `REPLACE_MORE_LIMIT = 32` near the top of `scrape.py`.

## Next steps (after data lands)
- `analyze.py` — sentiment + toxicity per comment, **per team**, with the
  r/soccerjerk-style sarcasm caveat handled by keeping sources separate.
- D3 timeline comparing the two finals side by side.
