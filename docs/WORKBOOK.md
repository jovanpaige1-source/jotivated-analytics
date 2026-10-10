# Jovan's dashboard: the workbook for Claude Code

You are Claude Code, working for Jovan Paige ("The Voice", Stay Jotivated). This
folder is his social analytics dashboard: Instagram, TikTok and YouTube, all
`notyo_averagejo`. It was built for him and arrives **already set up and filled**,
so most of `docs/SETUP-FOR-CLAUDE.md` is done. This workbook covers only what is
left on his Mac, the weekly refresh, and what to do when something breaks.

Read this whole file before running anything. Work one part at a time, show each
check, and only then move on.

## What is already done

| Piece | State |
|---|---|
| Handles | `scrape/handles.py`: `notyo_averagejo` on all three, YouTube channel `UCjz0bqe7SN8DSGFlYG2IiCQ`, `ENABLED = ["instagram", "tiktok", "youtube"]` |
| Data | First full pull on 2026-10-10: 684 Instagram posts, 244 TikToks, 95 YouTube Shorts |
| Topics | `scrape/categories.json`: ten topics built from his own captions (Motivation & Mindset, Emcee & Hosting, Keynotes & Youth, Atlanta & Community, Faith & Family, Brotherhood, Style & Apparel, The Book, Music & Culture, Travel) |
| Look | Stay Jotivated colors and fonts (`app/globals.css`, `app/fonts/`) |
| Not yet | His PIN, his dashboard Chrome window and sign-ins, TikTok Studio / YouTube Studio numbers, publishing |

The first pull read his **public** pages, so TikTok and YouTube have views but no
likes, comments, shares or saves yet. Part D fills those in from his own Studio.

## Rules (never break these)

- **Never ask for, accept or read a password, an API key or the PIN.** Jovan types
  his PIN into a hidden prompt in his own Terminal window. If he pastes a PIN or a
  hash into chat, tell him to pick a new one and do not use it.
- **Jovan signs in, not you.** You open the dashboard Chrome window; he signs in
  there. Never copy cookies or browser profiles, never automate a sign-in.
- **His accounts only.** Only `notyo_averagejo` and channels he names go in
  `scrape/handles.py`.
- **Nothing secret in git.** `.env.local` is gitignored. Run `git status` before
  every commit and stop if it lists `.env.local` or anything named like a key.
- **Show every command before you run it**, in one plain sentence. Never skip or
  disable a safety check, including the "Require a PIN" step in
  `.github/workflows/deploy.yml`.
- **Report honestly.** If a platform did not pull, say which one and why. A step is
  done only when its check passes.

## Part 0. Getting the folder onto his Mac

He receives it one of two ways. Ask which.

**A. GitHub transfer** (the repository moves to his GitHub account):
```
gh auth status
gh repo clone <his-github-username>/jotivated-analytics ~/projects/jotivated-analytics
cd ~/projects/jotivated-analytics
```

**B. A ZIP file:** unpack it to `~/projects/jotivated-analytics`, then make it his own
private repository:
```
cd ~/projects/jotivated-analytics
git init -b main
git add . && git commit -m "My Stay Jotivated dashboard"
gh repo create jotivated-analytics --private --source=. --remote=origin --push
```

Check: `ls scrape/handles.py public/data/instagram_posts.json` lists both files.

## Part A. Tools

Run these checks and install only what is missing (Homebrew: Jovan runs the
install line from brew.sh himself, it asks for his Mac password):
```
brew --version
git --version
gh auth status
node -v
pnpm -v
python3 -c "import websocket"
ls /Applications | grep -i chrome
```
Fixes: `brew install git gh node pnpm`, `python3 -m pip install websocket-client`,
`gh auth login` (he finishes it in the browser). Then:
```
pnpm install
```
Check: every tool prints a version; pnpm ends with a package summary.

## Part B. His PIN (he types it, you never see it)

Give him this line for **his own** Terminal window. It waits silently for four
digits and Return, then prints a 64 character fingerprint:
```
read -s PIN; printf '%s' "$PIN" | shasum -a 256 | cut -d' ' -f1; unset PIN
```
Then have him open `.env.local` and paste one line,
`NEXT_PUBLIC_DASHBOARD_PIN_HASH=<the fingerprint>`:
```
touch .env.local
open -e .env.local
```
Check: `test -f .env.local && echo ok` prints ok and `git status` does not list it.
Never `cat` that file.

Run it: start `pnpm dev` in the background, wait for "Ready", confirm
`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` prints 200. He opens
http://localhost:3000 and his PIN unlocks the dashboard with his numbers on it.

## Part C. The dashboard Chrome window and his sign-ins

The scraper reads through a separate Chrome window that carries his logins.
Chrome 136+ ignores the debugging port on an everyday profile, so it gets its own:
```
DIR="$HOME/.chrome-dashboard"
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="$DIR"
curl -s http://127.0.0.1:9222/json/version
```
In that new window, Jovan signs in to instagram.com, tiktok.com and youtube.com
(the Google account that owns the channel). Check: the curl prints a block starting
`"Browser": "Chrome/` and he confirms all three sign-ins.

This window must be open for every refresh. If it is closed, run the `open` line
again; the sign-ins are remembered in `~/.chrome-dashboard`.

## Part D. Exact likes, comments, shares and saves

With him signed in, the Studio pass (TikTok Studio, YouTube Studio) fills in what
the public pages hide. Run the first full pass (15 to 30 minutes, tabs open and
scroll by themselves):
```
python3 scrape/run.py --full
```
Check: the last line reads `done in ...: 3 ok, 0 failed`, and the `studio:` lines
show posts matched. If a studio line says SKIPPED, he is not signed in to that
Studio in the dashboard window: have him open studio.youtube.com or
tiktok.com/tiktokstudio there once, then rerun just that platform with
`--platforms tiktok` or `--platforms youtube`.

## Part E. The weekly refresh (the routine)

Every week (or before a sponsor meeting), with the dashboard Chrome window open:
```
cd ~/projects/jotivated-analytics
python3 scrape/run.py
git add public/data && git commit -m "Refresh data" && git push
```
The plain run is incremental: it stops each platform once it reaches posts it has
already seen, so it takes a few minutes. Report to Jovan, in this shape:

- new posts per platform and the follower counts (from the `instagram: +N new` lines)
- anything that failed, with the fix from the table below
- one thing worth his attention: the newest post in Insights > Viral Posts, or a
  topic in the Content Vault that moved

Want it on a schedule instead? Claude Code's `/schedule` (or a weekly reminder) can
run the same three lines, but only while the Mac is awake and the dashboard Chrome
window is open and signed in. Say that plainly; never promise an unattended refresh.

## Part F. His topics

`scrape/categories.json` decides the Content Vault. Each topic is a label plus
whole-word keywords matched against caption, title and hashtags. When he starts a
new series (a podcast, a tour, a new book), add a topic with five to fifteen
keywords taken from real captions, then:
```
python3 scrape/run.py --analyze-only
```
Check: it finishes in about a second and the Vault tab shows the new topic after
a reload. Posts that match nothing land in Other; if Other grows past a third of
all posts, read a sample of those captions and add keywords.

## Part G. Putting it online behind his PIN (optional)

GitHub Pages publishes on every push. Explain first: the published site is public
even when the repository is private (the PIN hides the page, it does not encrypt
the data files), and publishing from a private repository needs GitHub Pro.
Everything here is public profile data, so most people accept that.

```
gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow
```
Then he sets the PIN fingerprint as a repository secret, in his own Terminal:
```
read -s HASH; gh secret set DASHBOARD_PIN_HASH --body "$HASH"; unset HASH
```
Publish and confirm:
```
git push
gh run watch
curl -s -o /dev/null -w "%{http_code}" https://<his-user>.github.io/jotivated-analytics/
```
Check: the run is green, the address returns 200, his PIN opens it and a wrong one
does not.

## When something breaks

| Message or symptom | What it means | Fix |
|---|---|---|
| `REFUSED: ... 9222` | The dashboard Chrome window is closed | Run the Part C `open` line, then retry |
| `Instagram shows the login wall` | Signed out of Instagram in that window | He signs in there, rerun `--platforms instagram` |
| `view enrichment stopped` with a status | Instagram is throttling play-count lookups | Normal; the rest fill in on the next refresh. Never retry in a loop |
| `studio: SKIPPED` | Not signed in to TikTok Studio / YouTube Studio | Part D |
| `dates filled ... remaining N` | Some YouTube dates did not load this run | They fill on the next refresh |
| Instagram followers look rounded (17.0K) | Instagram only shows a rounded count publicly | Expected |
| A new topic does not show | Analyze did not rerun | `python3 scrape/run.py --analyze-only`, reload |
| Comments tab is empty | No reader collects comments yet | Expected; say so, do not invent numbers |
| Styles look stale in `pnpm dev` | Next's dev cache | `rm -rf .next/dev .next/cache` then restart |
| `gh run watch` fails at "Require a PIN" | The `DASHBOARD_PIN_HASH` secret is missing | Part G secret step; never remove the check |

## Adding Facebook later

His Facebook page (`facebook.com/stayjotivated`) needs a sign-in to view and has no
reader yet. The clean route is Meta's Page Insights through his own Meta Business
access, built as a new `scrape/platforms/facebook.py` plus `"facebook"` in the
`Platform` type, `ENABLED` and `PLATFORMS`. That is a build, not a refresh: tell
Jovan it is a project, not something to improvise.
