# For Claude Code: the setup as a checklist

> In Jovan's copy (`jotivated-analytics`), `docs/WORKBOOK.md` replaces this
> checklist: it is already set up and filled. Keep this file as reference only.

You are reading this because a person wants this dashboard set up and asked
you to do it. Assume they have never used Terminal unless they say otherwise.
The human guide (`docs/Setup-Guide.pdf`, same text in `docs/setup-guide.html`)
is the source of truth for every command and every "Expect" line. This file is
the order of work, the checks, and the rules. Work one part at a time, show the
checkpoint, and only then move on.

If you are reading this inside an already cloned copy, Part C1 is done. Start at
the first check that fails.

## Rules

- **Never ask for, accept or read a password, an API key or the PIN.** Not in
  chat, not from a file. The PIN steps (C2, H2) are typed by the person into a
  hidden prompt in their own Terminal window; you give them the exact line and
  wait. If they paste a PIN or a hash into the chat anyway, tell them to pick a
  new one and do not use it.
- **Show every command before running it**, in one plain sentence plus the
  command. Never disable, skip or work around a safety check, including the
  "Require a PIN" step in `.github/workflows/deploy.yml`.
- **The person signs in.** You open the dashboard Chrome window (D1); they sign
  in to each platform there. Never copy cookies, profiles or Login Data, and
  never automate a sign-in.
- **Their accounts only.** Only the handles they give you go in
  `scrape/handles.py`. Read LinkedIn at most once a day.
- **Nothing secret in git.** `.env.local` stays untracked. Run `git status`
  before every commit and stop if it lists `.env.local` or anything with "key"
  in the name.
- **When a step fails,** read the error and the fixes table in the guide before
  retrying. A platform "login" or "checkpoint" means the person needs to sign
  in again in the dashboard Chrome window; say so and wait. Never retry a 429
  in a loop.
- **Report honestly.** If a platform did not pull, say which and why. Never
  call a step done without its check passing.

## Order of work

### A. Tools

You: run the six checks and install only what is missing, with the guide's
Part A commands.

```
brew --version
git --version
gh auth status
node -v
pnpm -v
python3 -c "import websocket"
ls /Applications | grep -i chrome
```

The person: runs the Homebrew install line themselves if Homebrew is missing
(it asks for their Mac password), and completes `gh auth login` in the browser
when it opens.

Check: every tool answers with a version; `gh auth status` names their account.

### C1. Their own copy

Ask for one privacy choice first: private plus local, private plus hosted, or
public plus hosted. Unpack the paid template ZIP into
`~/projects/social-analytics-dashboard`, then run:

```
cd ~/projects/social-analytics-dashboard
git init -b main
git add . && git commit -m "Start my creator analytics dashboard"
gh repo create social-analytics-dashboard --private --source=. --remote=origin --push
pnpm install
```

Use `--private` for either private path. Replace it with `--public` only when
the person chooses free hosted Pages and accepts that the source and data files
will be public. Private hosted Pages requires GitHub Pro, Team or Enterprise,
and the published Pages site is still public. Private plus local skips Part H.

The person confirms the repository name, privacy choice and any paid GitHub
plan required for private hosted Pages.

Check: `gh repo view --json visibility -q .visibility` prints the intended
visibility. The folder has `package.json`, `scrape/` and `public/data/`, and
pnpm ends with a package summary.

### C2. Their PIN (they type it, you never see it)

Give them this line to run in their own Terminal window. It waits silently for
four digits and Return, then prints a 64 character fingerprint:

```
read -s PIN; printf '%s' "$PIN" | shasum -a 256 | cut -d' ' -f1; unset PIN
```

Then the three commands to put it in `.env.local` (they paste the fingerprint
into the editor that opens, as `NEXT_PUBLIC_DASHBOARD_PIN_HASH=<fingerprint>`):

```
touch .env.local
open -e .env.local
```

Check: `test -f .env.local && echo ok` prints ok; `git status` does not list
it. Never `cat` the file.

### C3. Run it locally

You: start `pnpm dev` in the background, wait for "Ready", then check
`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` prints 200.

The person: opens localhost:3000 in Chrome and enters their PIN.

Check: they confirm the PIN unlocks an empty dashboard with five tabs.

### D1. The dashboard Chrome window

You:

```
DIR="$HOME/.chrome-dashboard"
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="$DIR"
curl -s http://127.0.0.1:9222/json/version
```

The person: signs in to each platform they use, in that new window only.

Check: the curl prints a block starting `"Browser": "Chrome/`; they confirm
the sign-ins.

### E. Their accounts

Ask which platforms they use and their usernames (no @, except YouTube's
handle). For YouTube, walk them to YouTube Studio, Settings, Channel, Advanced
settings for the 24 character channel ID starting `UC`. Edit
`scrape/handles.py` with exactly what they gave you.

Check, from the project folder:

```
python3 -c "from scrape.handles import HANDLES; print(HANDLES)"
```

shows their names, no placeholders.

### F1. The first pull

Say it takes 15 to 30 minutes and that tabs will open and scroll on their own.
Run in the background and report progress every few minutes from its output:

```
python3 scrape/run.py --full --platforms <their list>
```

Check: the last line reads `done in ...: N ok, 0 failed`. If one failed, name
it, apply the fixes table, and rerun only that platform with
`--platforms <name>`.

### G. Their topics

Ask what they post about (four to eight topics). Rewrite
`scrape/categories.json` with those labels and keywords, picking keywords from
a sample of captions in `public/data`. Keep "other". Then:

```
python3 scrape/run.py --analyze-only
```

Check: finishes in under a second; the Vault tab shows their topics after a
reload.

### H1. Turn on Pages

Skip all of H for private plus local. For private plus hosted, confirm the
person has GitHub Pro, Team or Enterprise. Explain that a normal GitHub Pages
site is still public even when the source repository is private.

```
gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow
```

A 409 means it is already on. If the call is refused, the person does it in
Settings, Pages, Source = GitHub Actions.

Check: `gh api repos/{owner}/{repo}/pages` returns `"build_type": "workflow"`.

### H2. The PIN fingerprint as a secret (they type it)

Give them this line to run in their own Terminal window, in the project folder.
They paste the same 64 character string from C2 into the hidden prompt:

```
read -s HASH; gh secret set DASHBOARD_PIN_HASH --body "$HASH"; unset HASH
```

Check: `gh secret list` shows `DASHBOARD_PIN_HASH`.

### H3. Publish

```
git status
git add public/data
git commit -m "First data pull"
git push
gh run watch
curl -s -o /dev/null -w "%{http_code}" https://<user>.github.io/social-analytics-dashboard/
```

Stop at `git status` if it lists `.env.local`. The person opens the address
and enters their PIN, and tries a wrong one too.

Check: the run is green, the URL returns 200, their PIN unlocks it and a wrong
one does not.

## Skip what does not apply

If they want the dashboard on their Mac only, stop after G and skip H. If they
use fewer platforms, list only those in F1 and never add a platform they did
not name. If a page or tool refuses you (a 403, a rate limit, a sign-in wall),
report it and wait; do not look for another way in.

## The final report

End with: the dashboard address (or "on your Mac at localhost:3000"), how many
posts came in per platform, the three line routine ready to paste:

```
cd ~/projects/social-analytics-dashboard
python3 scrape/run.py
git add public/data && git commit -m "Refresh data" && git push
```

the rule that the dashboard Chrome window must be open for every pull, and
what a "login" message means. Then offer the one change most worth making
next: topics in Part G if they skipped it, or LinkedIn if they have not signed
in there yet.
