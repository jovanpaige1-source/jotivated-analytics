# Creator Dashboard scraper

Python (stdlib + `websocket-client`) that re-scrapes Instagram / TikTok /
YouTube / Threads / LinkedIn through the dashboard Chrome window (setup guide,
Part D1), then rebuilds every derived JSON the dashboard reads.

One time:

```bash
python3 -m pip install websocket-client
```

## Run it

From the project folder (`cd ~/projects/jotivated-analytics`):

- `python3 scrape/run.py` incremental, every platform in `ENABLED` in
  `scrape/handles.py` (Instagram, TikTok and YouTube in this copy)
- `python3 scrape/run.py --platforms instagram` one platform
- `python3 scrape/run.py --full` master sweep (see below)
- `python3 scrape/run.py --analyze-only` just rebuild the analytics and vault JSON

Keep `#` comments out of lines you paste into Terminal. The Mac's zsh passes
them to the command as extra words.

Then commit `public/data/` and push. GitHub Pages redeploys in about a minute.

The dashboard's **Refresh data** menu does the same thing through
`scrape/server.py` (port 5556). It only shows when the dashboard runs on your
Mac at `localhost:3000`, and the service only answers that page. Start it with
`python3 scrape/server.py` in its own Terminal window. Send `{"mode": "full"}`
in the POST body for a sweep.

## Incremental vs. master sweep

**Incremental** is the default and what you want day to day. Each platform
pages newest-first and stops after it has seen 8 posts in a row that are
already in `public/data/<platform>_posts.json` (Threads uses 32 because its
pages are large). Only new posts are added; older posts keep the metrics
from whichever scrape saw them last. A typical run touches a few dozen
posts and finishes in a couple of minutes.

**Master sweep** (`--full`) ignores that early stop and pages every profile
to the end, refreshing views, likes, and comments on every post. Budget
15 to 30 minutes and expect TikTok to be the slow one (it scrolls the DOM).
Run it deliberately, not on a schedule.

## Chrome

Start the dashboard Chrome window with the lines in setup guide Part D1:

```bash
DIR="$HOME/.chrome-dashboard"
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="$DIR"
```

Chrome 136 and later ignore `--remote-debugging-port` on your everyday
profile, so the window needs its own profile (`--user-data-dir`). Sign in to
each platform in it once and it remembers them. The reader connects on
`CHROME_CDP_PORT` (default 9222), opens its own tabs there and closes only
those. If a platform is logged out, sign in to it in that window and rerun
for that platform only.

## What gets written

| File | Written by | Purpose |
|---|---|---|
| `public/data/<platform>_posts.json` | `platforms/*.py` | raw posts, merged incrementally |
| `public/data/scrape_state.json` | `server.py` / `run.py` | per-platform status, last run, follower counts |
| `public/data/analytics.json` | `analyze.py` | every Insights section (heatmap, viral, hooks, hashtags, superfans, ...) |
| `public/data/content_vault.json` | `analyze.py` | Content Vault: posts grouped by topic |
| `public/data/follower_history.json` | `analyze.py` | one follower snapshot per scrape day (appended, never rewritten) |

No reader collects comments or follower lists yet, so `comments.json` and
`follow_data.json` stay empty, and the Comments tab, Top questions and
Superfans show nothing.

### Comment sentiment

This only matters once `comments.json` holds comments. `analyze.py` labels
every comment through `scrape/sentiment.py` and writes the labels back into
`comments.json` (`sentiment`, `isQuestion`, `sentimentSource`,
`sentimentV`). The file is the cache: only comments without a current label are
touched on each run. Two paths:

- **Model** (preferred): Groq's free tier, key from Keychain. Never put the key
  in a file. Pass it from Keychain as an environment variable for one command:

  ```bash
  GROQ_API_KEY="$(security find-generic-password -a "$USER" -s GROQ_API_KEY -w)" python3 scrape/run.py --analyze-only
  ```

  Rows the model could not label keep the lexicon label and are retried next
  run.
- **Lexicon** (fallback): emoji-aware, word-boundary, negation-aware, tuned for
  creator comments (congrats, fire, goat, salute, facts). Runs without a key in
  well under a second. Bump `SENTIMENT_VERSION` after changing either the
  lexicon or the prompt to relabel everything.

A question is a separate flag, not a sentiment, so "Amazing! What camera is
that?" is both positive and a question.

## Topics (Content Vault)

`scrape/categories.json` maps a topic slug to a label and a keyword list.
Matching is whole-word and case-insensitive against title + caption +
hashtags. A post can land in several topics; anything matching nothing goes
to `other`. Add or move keywords, then:

```bash
python3 scrape/run.py --analyze-only
```

No code change is needed to add a topic.

## Layout

```
scrape/
├── run.py            command line runner
├── server.py         HTTP service for the dashboard's Refresh button (:5556)
├── analyze.py        rebuilds analytics.json, content_vault.json, follower_history.json
├── categories.json   editable topic keyword map
├── cdp.py            Chrome DevTools Protocol client (own-tab discipline)
├── incremental.py    load/merge helpers + STOP_AFTER_KNOWN
├── handles.py        your handle per platform
└── platforms/
    ├── instagram.py  web_profile_info + feed API via fetch() in page context
    ├── tiktok.py     DOM tile extraction while scrolling
    ├── youtube.py    ytInitialData + innertube continuations (videos + shorts)
    ├── threads.py    XHR hook capturing /graphql/query while scrolling
    └── linkedin.py   reads the rendered activity feed cards (no catchable XHR); likes are its reach
```
