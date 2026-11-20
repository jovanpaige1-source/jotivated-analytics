@AGENTS.md

> **This copy belongs to Jovan Paige (Stay Jotivated, `notyo_averagejo`).** It is
> already configured and filled. For setup on his Mac, the weekly refresh and
> troubleshooting, follow `docs/WORKBOOK.md` first; it overrides the template
> notes below. Only Instagram, TikTok and YouTube are enabled
> (`scrape/handles.py` ENABLED, `lib/derive.ts` PLATFORMS).
>
> On this Mac this folder is ~/Jotivated/jotivated-analytics. Where the docs say
> ~/projects/jotivated-analytics, they mean this folder. If git remote prints nothing
> there is no GitHub copy: end Part E at the commit and skip git push.
>
> This Mac is a 2015 Intel MacBook Air on macOS 12 with 4 GB RAM, so there is **no
> Homebrew**. Node.js 22 comes from the official nodejs.org installer (/usr/local/bin),
> pnpm 10 is in ~/.local/bin (`npm install -g --prefix ~/.local pnpm@10`), git and
> Python 3.9 come from Apple's Command Line Tools, and websocket-client is a
> `pip install --user`. Never run `brew` here. Refreshes are slow; tell him to close
> other apps first. jotivated-studio is not set up on this Mac (Intel/4 GB cannot run it).

# Social Analytics Dashboard: project brain

## What this is
A creator analytics dashboard for Instagram, TikTok, YouTube, Threads and
LinkedIn. Next.js 16 + Tailwind v4 + shadcn/ui, exported as a static site to
GitHub Pages. A Python `scrape/` pipeline (scrapers → `analyze.py` → derived
JSON) fills `public/data/`. This repo is a template: the data files start
empty and `scrape/handles.py` holds placeholders.

**Setting this up for someone?** Follow `docs/SETUP-FOR-CLAUDE.md`: the order
of work, the checks, and the rules (never handle their PIN, password or keys;
they sign in to the dashboard Chrome window themselves).

## Stack
- Next.js 16 App Router · TypeScript · Tailwind v4 · shadcn/ui
- Recharts (line/bar/doughnut). The 7×24 heatmap is hand-rolled.
- Zustand + localStorage persistence (key: `creator_dashboard_v2`)
- Fonts: Archivo (body) and Big Shoulders (display), local woff2 in
  `app/fonts/`, loaded with `next/font/local` in `app/layout.tsx`
- Python 3.9+ standard library plus `websocket-client`

## Tabs
| Tab | Route | Component | Reads from |
|---|---|---|---|
| Overview | `/` | `components/overview/overview.tsx` | posts × 5, scrape_state, follower_history, content_vault |
| Post Analysis | `/posts` | `components/posts/posts.tsx` | posts × 5 |
| Comments | `/comments` | `components/comments/comments.tsx` | comments |
| Insights | `/insights` | `components/insights/insights.tsx` | analytics, follow_data |
| Content Vault | `/vault` | `components/vault/vault.tsx` | content_vault + posts × 5 |

## Design system (don't drift)
- Stay Jotivated palette: stone background `#f2f0ec`, red brand `#be1d19` as
  the single accent, white cards. The tokens in `app/globals.css` `:root` are
  the source of truth.
- Text: `#0b0b0b` ink, `#2e2e2e` soft, `#6b6b6b` muted.
- Positive `#16a34a`, Negative `#dc2626`, Warn `#d97706`, sparingly.
- Per-platform colors live in `app/globals.css` (`--ig`, `--tt`, `--yt`, `--th`, `--li`).
- Every tab opens on one dark hero band (`PageHero`); everything else is light cards.
- Display numerals align by ink via `numeralShift()` in `lib/format.ts`.
- Phone width is part of done: every `main .card` must have
  `scrollWidth <= clientWidth + 2` and a width no greater than the viewport
  at 375px; responsive grids need a `grid-cols-1` base; category bar charts
  pass `shortLabels` so every bar stays labeled.

## Data rules
- `public/data/*.json` is read by `fetch()` at runtime; every loader in
  `lib/data.ts` has a fallback, so an empty file never breaks a page.
- Derived files are generated, never hand-edited: `analytics.json`,
  `content_vault.json`, `follower_history.json` come from `scrape/analyze.py`.
  Topics live in `scrape/categories.json`.
- Threads and LinkedIn publish no view count (`VIEWLESS_PLATFORMS` in
  `lib/derive.ts`): likes are their reach, engagement is against followers.
  Never show `n/a` for them and never add their likes into a views total.
- Comments: `scrape/platforms/comments.py` (added 2026-11-20) reads top-level
  comments on his own Instagram, TikTok and YouTube posts after each post
  reader, gently: only posts whose comment count changed
  (`public/data/comments_state.json`), newest first, up to 60 per post and 40
  posts per platform per run (150 with `--full`), so the backlog fills over
  several refreshes. `--comments-only` reads just comments; `--no-comments`
  skips them. Replies and his own comments are not stored; YouTube dates are
  approximate (YouTube gives "3 weeks ago"). `follow_data.json` still stays
  empty: no follower-list reader exists. Sentiment is labeled by `scrape/sentiment.py` at analyze time and cached in
  `comments.json` (`sentiment`, `isQuestion`, `sentimentSource`,
  `sentimentV`). The UI never re-classifies.
- The public TikTok and YouTube pages give views only. `scrape/platforms/
  studio.py` runs after each of those readers (skip with `--no-studio`): it
  hooks the studio page's own list requests, drives the page (TikTok twice,
  by date and by views, since either sort alone skips posts; YouTube through
  its pages and Shorts tab) and writes exact likes, comments, shares and saves,
  stamping each post `engagementMeasured`. `engagementMeasured()` in
  `lib/derive.ts` and `_has_engagement()` in `scrape/analyze.py` count a
  stamped post, or one with any figure filled, and skip the rest, so a pull
  without a studio sign-in never averages zeros. Never replay a studio
  request: both are signed per request by the page.
- `analyze.py` only appends a follower snapshot on a day a scrape ran.

## Scraper rules
- Uses the dashboard Chrome window from docs/WORKBOOK.md Part C (port 9222). Opens
  its own tabs and closes only those. Chrome 136 and later ignore
  `--remote-debugging-port` on the default profile, so D1 starts a separate
  profile with `--user-data-dir="$HOME/.chrome-dashboard"`. If port 9222 is
  closed, tell the user to run D1. Never quit or relaunch their everyday Chrome.
- LinkedIn is read from the rendered activity feed; never read messaging.
- A login wall raises a clear error for that platform; the others continue.
- `python3 scrape/run.py` (incremental), `--full` (sweep), `--analyze-only`.

## PIN gate
- SHA-256 client-side check, `sessionStorage["dashboard_auth"]`.
- Hash from `NEXT_PUBLIC_DASHBOARD_PIN_HASH`; the repo may be public, so the
  PIN itself never goes into a tracked file. Set the GH secret
  `DASHBOARD_PIN_HASH` for production.
- No fallback PIN in a production build. Without a hash, `pnpm build` renders a
  "No PIN set" screen and the deploy workflow fails before building. `pnpm dev`
  alone accepts the development PIN 0000 until `.env.local` exists. Never add
  a real PIN's hash to the code.

## Deploy
- `.github/workflows/deploy.yml` builds with
  `NEXT_PUBLIC_BASE_PATH=/<repository name>` (derived automatically) and
  publishes `out/` to GitHub Pages on every push to `main`.
