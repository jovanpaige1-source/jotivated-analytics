# Creator Analytics Dashboard: Complete DIY Template

A PIN-gated, zero-cost analytics site for a creator's Instagram, TikTok,
YouTube, Threads and LinkedIn. Static Next.js on GitHub Pages, and a Python
scraper that reads the platforms through a separate Chrome window you sign in
to. Comments are not collected yet, so the Comments tab stays empty.

**Start here:** `docs/Setup-Guide.pdf` walks from a blank Mac
to a live site and assumes no prior experience with Terminal, GitHub or
Claude Code. The same guide is in `docs/setup-guide.html`.

**The short way:** let Claude Code do the setup. Install it
(https://code.claude.com/docs/en/quickstart), open Terminal in the folder
where you want the project and type `claude`, then paste:

> Read docs/Setup-Guide.pdf from this project. At the end there is a section called "For Claude
> Code: the setup as a checklist". Follow it and set the dashboard up for me,
> one part at a time. Never ask me for a password, a key or my PIN; the
> checklist says which steps I do myself.

Inside a cloned copy the same checklist is `docs/SETUP-FOR-CLAUDE.md`, so a
Claude working in this folder can read it directly.


## Quick start

1. Unpack the paid template ZIP into `~/projects/social-analytics-dashboard`.
2. Create your own private repository with `gh repo create social-analytics-dashboard --private --source=. --remote=origin --push`.
3. Run `pnpm install` and `python3 -m pip install websocket-client`.
4. Put your handles in `scrape/handles.py`.
5. Open the dashboard Chrome window (setup guide, Part D1) and sign in to your
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
public/data/    the JSON the site reads (empty in the template, the scraper fills it)
docs/           the setup guide
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
