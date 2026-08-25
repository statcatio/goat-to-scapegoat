# Design

<!-- impeccable:design-schema 1 -->

Visual world for **From GOAT to Scapegoat**. Committed direction: **The Statistical
Almanac** — Swiss / mid-century sports-annual restraint. Credibility comes from
objective typography and disciplined data, not from decoration. This is a
deliberate single-light world (print paper); it does not invert for dark mode.

## Color

Restrained strategy: warm paper ground + ink, with **one** brand accent. A second
data color exists only as a *semantic role inside charts*, never as decoration.

| Token | Value | Role |
|---|---|---|
| `--paper` | `#EFF3E3` | Page ground (the user's pinned color) |
| `--paper-2` | `#E5EAD5` | Recessed blocks, chart tracks |
| `--ink` | `#1C1A14` | Primary text, wordmark (warm near-black) |
| `--ink-2` | `#5B5647` | Secondary text — warm taupe, tinted from ink, **never gray** |
| `--rule` | `rgba(28,26,20,0.22)` | Hairlines |
| `--accent` | `#3C6E9F` | Argentina sky-blue — chart fills only |
| `--accent-ink` | `#2E5A85` | Accent when used as text (contrast-safe on paper) |
| `--neg` | `#9E4A34` | Data role: negative / against sentiment. Not a brand color. |

Contrast: all text ≥4.5:1 on paper. Secondary text is tinted warm, not gray.

## Type

System neo-grotesque (Swiss register) — credibility over character. No literary
serif display (that is the cliché this world refuses). Webfonts are avoided
(CSP + silent-fallback risk); the stack is the design.

- **Display / wordmark:** `"Helvetica Neue", Helvetica, Arial, sans-serif`, weight
  700–800, uppercase, tracking `-0.03em`, line-height ~0.95. Left-aligned, never
  centered.
- **Body:** same family, 400/500, measure 62–72ch, line-height 1.5.
- **Labels / kickers:** same family, uppercase, tracking `0.12em`, `--ink-2`.
  One named kicker per block — never a tracked eyebrow over every section.
- **Figures:** `font-variant-numeric: tabular-nums` in the grotesque (almanac
  tables use aligned lining figures, not monospace costume).

## Composition

- **Masthead, not hero.** Open like an almanac page: a thin meta rule (title of
  record + source), the wordmark, a one-line dek, then data immediately.
- **Data is the ornament.** The signature element is a diverging results table —
  a zero baseline with sentiment extending right (positive, accent) or left
  (negative, `--neg`), so the *flip* between 2022 and 2026 is the visual.
- Hairline rules and generous whitespace do the structuring. No cards, no boxes,
  no shadows (this is flat print). More space above a heading than below it.
- Tabular figures right-aligned in their own column.

## Motion

One authored moment only: on load, the diverging bars grow from the zero
baseline (exponential ease-out), content already visible behind them. No
scattered hover effects, no per-section entrances. Fully static under
`prefers-reduced-motion`.

## Honesty rule (from PRODUCT.md)

No real Reddit data is scraped yet. Any figure shown is **clearly labeled as
sample / illustrative** until real data lands. Never present synthetic numbers as
findings.
