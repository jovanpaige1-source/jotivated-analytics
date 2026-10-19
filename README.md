# Stay Jotivated Analytics

Jovan Paige's private analytics dashboard: Instagram, TikTok and YouTube
(`notyo_averagejo`) in one place, behind a PIN. Static Next.js site plus a
Python scraper that reads the platforms through a separate Chrome window he
signs in to. Built and filled by Intellovate on 2026-10-10.

**Before you start:** you need a paid Claude plan and Claude Code on your Mac.
Install it with Anthropic's Claude Code quickstart (or, if you already have
Homebrew, `brew install --cask claude-code`), then check it in Terminal with
`claude --version`. This folder belongs at `~/projects/jotivated-analytics`.

**Jovan, start here:** open Terminal, go to this folder with
`cd ~/projects/jotivated-analytics`, start Claude Code with `claude`, and paste:

> Read docs/WORKBOOK.md and set up my dashboard, one part at a time. Never ask
> me for a password, a key or my PIN; the workbook says which steps I do myself.

**Every week after that:**

> Read docs/WORKBOOK.md Part E and refresh my dashboard.

`docs/WORKBOOK.md` is the handover: what is done, what is left on his Mac, the
weekly refresh, topics, publishing, and fixes. The template's own setup checklist
(`docs/SETUP-FOR-CLAUDE.md`) is kept as reference.

## Quick start (the general template, for reference)

Jovan's copy is already past most of this. On his Mac, follow
`docs/WORKBOOK.md` instead; the folder and repository are named
`jotivated-analytics`, not `social-analytics-dashboard`.

1. Unpack the paid template ZIP into `~/projects/social-analytics-dashboard`.
2. Create your own private repository with `gh repo create social-analytics-dashboard --private --source=. --remote=origin --push`.
3. Run `pnpm install` (pnpm 10: `npm install -g pnpm@10`; pnpm 12 stops on
   this lockfile) and `python3 -m pip install websocket-client`.
4. Put your handles in `scrape/handles.py`.
5. Open the dashboard Chrome window (docs/WORKBOOK.md, Part C) and sign in to your
   accounts in it the first time. Chrome 136 and later ignore
   `--remote-debugging-port` on your everyday profile, so it needs its own:

   ```
   DIR="$HOME/.chrome-dashboard"
   open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="$DIR"
   ```
6. `python3 scrape/run.py --full` for the first pull, then `pnpm dev`.
7. If you chose hosting, open Settings, Pages and set Source to GitHub Actions. Set the
   `DASHBOARD_PIN_HASH` secret, then push. The site publishes on every push.

Details, expected output for every step, and troubleshooting are in the guide.

A private repository works with the complete local dashboard on GitHub Free. Publishing GitHub Pages from a private repository requires GitHub Pro, Team or Enterprise, and the normal Pages site is still public. For the strongest privacy covered here, keep the repository private, run locally and skip publishing.

## Layout

```
app/            one route per tab
components/     charts, layout, overview, posts, comments, insights, vault
lib/            data loaders, calculations, formatting, PIN check, types
scrape/         run.py, analyze.py, sentiment.py, categories.json, handles.py, platforms/
public/data/    the JSON the site reads (filled with Jovan's posts, the scraper refreshes it)
docs/           WORKBOOK.md (the handover) and the template's setup checklist
```

## Rules

- Never commit a PIN or an API key. The PIN is a SHA-256 hash in a GitHub
  secret. It is a light lock: a four digit PIN can be worked out from its
  hash, so use one you use nowhere else.
- The scraper opens its own Chrome tabs and closes only those. It never
  copies cookies and never reads LinkedIn messaging.
- Threads and LinkedIn publish no view counts, so the dashboard shows likes as
  reach for them instead of zeros. The public TikTok and YouTube pages give
  views only, so after each of those readers the scraper opens TikTok Studio
  and YouTube Studio in the same signed-in window and fills in exact likes,
  comments, shares and saves. If you are not signed in there, the pass is
  skipped, those posts stay at 0 and are left out of engagement averages.
