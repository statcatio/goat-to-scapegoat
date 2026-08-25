# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: general soccer- and culture-interested readers who arrive via a shared
social link (LinkedIn, Instagram, Reddit). Mostly non-technical, scrolling on
desktop or phone, deciding in a few seconds whether to stay. Many have felt the
"hate-watch" turn against Argentina themselves, or are curious why their feeds
soured on a team they once celebrated. Recruiters and the data community are a
welcome secondary audience, but the data craft is in service of the story, not
the reason people come.

## Product Purpose

A data-driven narrative investigating how online sentiment toward Argentina's
national team shifted between two World Cup finals — 2022 (won; Messi crowned the
undisputed GOAT) and 2026 — using real Reddit match-thread reactions. It exists
to pose, and let the reader *feel*, one question: **did Argentina actually
change, or did we?** Success = a broad reader is pulled through the piece, feels
the hook, and shares it.

## Positioning

A "sentiment autopsy" comparing the **same team across two finals** using
per-team sentiment/toxicity drawn from real Reddit discourse. It measures the
*discourse about* Argentina rather than issuing a verdict on their conduct. The
across-time comparison — and the honest, curious framing — is what a hot-take
article or a single-tournament recap could not truthfully copy.

## Operating Context

Encountered as a link from a social feed and typically read start-to-finish in
one sitting, on desktop or phone. First touch is almost always a scroll out of a
crowded feed, so the piece competes for the first few seconds against everything
else there. Readers arrive with strong priors about Argentina, Messi, and the
"hate-watch" phenomenon. An interactive timeline invites exploration, but the
core story must land even for a passive scroller who never interacts.

## Capabilities and Constraints

- **Data source:** Reddit match-thread comments via the official API (PRAW) —
  the two final threads (2022 ARG–FRA `zoz9vx`; 2026 ESP–ARG `1v0wji4`).
  Anonymous scraping is hard-blocked (403); authenticated API access is required.
- **Analysis:** comment-level sentiment + toxicity, bucketed *per team*
  (sentiment toward Argentina vs. the opponent) via name/player keyword matching.
- **Known caveat:** satire/sarcasm sources (e.g. r/soccerjerk) break off-the-shelf
  sentiment models; sources are kept separate rather than pooled into one average.
- **Visualization:** a timeline is the intended centerpiece (D3, for flexibility),
  tracking comment volume and sentiment across the match.
- **Effort/scope:** a focused, largely single-narrative web piece built in a small
  time budget (~10 hours of work), not a large multi-page application.
- **Undecided (not locked):** whether the piece stays strictly two-final or later
  expands to more matches/subreddits was explicitly *not* made binding.

## Brand Commitments

- **Name: From GOAT to Scapegoat** — confirmed binding, including the
  goat/scapegoat wordplay.
- **Voice** (from the author's own framing): personal, honest, self-aware; opens
  with the maker's own arc from lifelong Messi fan to rooting against Argentina;
  curious rather than accusatory.
- Recorded as *current approach, revisable* (the user did not mark these binding):
  the neutral "measure, don't judge" stance, and the strict two-final structure.

## Evidence on Hand

- Two real Reddit threads identified (IDs above). **No comments have been scraped
  yet** — as of now there is zero analyzed data. Future work must not fabricate
  sentiment numbers, comments, or findings; any placeholder must be clearly
  labeled synthetic until real data lands.
- A drafted narrative and voice exist: the author's personal arc; the 2022
  "¿Qué mirás, bobo?" Messi moment and the mocking of the Netherlands coach; and
  booing of Messi witnessed in person during the 2026 final.
- An incumbent landing hero (`landing.html`) exists — treated as evidence and
  anti-reference for later visual decisions, not as a locked design (the author
  liked its copy but not its visual direction).

## Product Principles

1. **Story first, data in service of it** — the reader is a scroller from a feed,
   not an analyst; craft earns attention but never becomes the subject.
2. **Measure the discourse, not the team** — show what people said and when it
   shifted; avoid asserting Argentina's guilt.
3. **Honest about the data** — surface caveats (sarcasm, sample size) rather than
   hiding them; never fabricate.
4. **The hook is the through-line** — every section serves "did they change, or
   did we?"
5. **Works passively, rewards actively** — lands for a skimmer, deepens for anyone
   who explores the timeline.

## Accessibility & Inclusion

Shared broadly and read on phones as much as desktop: must be responsive and
legible on small screens, meet sufficient text/UI contrast, and keep the
interactive timeline keyboard-operable and respectful of reduced-motion
preferences. No stricter product-specific standard has been established.
