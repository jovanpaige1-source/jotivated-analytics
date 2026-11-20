"""
Comment reader: top-level comments on his own posts, all three platforms.

Runs after each platform's post reader (scrape/run.py and the Refresh button).
Every request goes through one tab this module opens in the dashboard Chrome
window, so the platform's own signed-in session and request signing apply.
Verified 2026-11-20 from that window:

  instagram  GET  /api/v1/media/<pk>/comments/   (X-IG-App-ID, 15 per page, min_id paging)
  tiktok     GET  /api/comment/list/?aweme_id=   (the page's fetch signs it, 20 per page, cursor)
  youtube    POST /youtubei/v1/next              (token from the watch page, 20 per page)

Gentle on purpose (about 17,500 comments across ~900 posts at the time):
  - only posts whose comment count changed since they were last read
    (public/data/comments_state.json), newest first
  - at most PER_POST top-level comments per post, sorted the platform's way
    (Instagram/YouTube put the top comments first)
  - at most POSTS_PER_RUN posts per platform per run, more on --full, with a
    pause between requests. The backlog catches up over a few refreshes.
  - any 4xx/5xx or non-JSON answer stops that platform for this run and
    keeps what was read; never retried in a loop.

Replies are not read. His own comments (his replies on his posts) are skipped
so he never shows up as his own top commenter. YouTube only gives relative
times ("3 weeks ago"), so a YouTube comment's date is approximate and fixed
the first time it is seen.

Writes public/data/comments.json in the shape lib/types.ts Comment expects;
analyze.py labels sentiment and questions afterwards.
"""

from __future__ import annotations

import json
import random
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from scrape.cdp import CDP, CDPError
from scrape.handles import HANDLES

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "public" / "data"
COMMENTS_FILE = DATA_DIR / "comments.json"
STATE_FILE = DATA_DIR / "comments_state.json"
POST_FILES = {p: DATA_DIR / f"{p}_posts.json" for p in ("instagram", "tiktok", "youtube")}

PER_POST = 60
POSTS_PER_RUN = 40
POSTS_PER_RUN_FULL = 150
PAUSE_MS = 1400  # between requests inside a post, plus jitter
PAUSE_BETWEEN_POSTS = 1.5  # seconds

OWN = {h.lstrip("@").lower() for h in HANDLES.values()}

PAGE_URLS = {
    "instagram": f"https://www.instagram.com/{HANDLES['instagram']}/",
    "tiktok": f"https://www.tiktok.com/@{HANDLES['tiktok']}",
    "youtube": f"https://www.youtube.com/{HANDLES['youtube']}/shorts",
}

# One page per call, so no single evaluate runs long (a slow Mac timed out
# at 30 s when a whole post was read in one call). Each returns
# {ok, status?, error?, items: [...], next: cursor-or-null}.
_JS_PAGE = {
    "instagram": """
const url = '/api/v1/media/%(key)s/comments/?can_support_threading=true&permalink_enabled=false'
  + (%(cursor)s ? '&min_id=' + encodeURIComponent(%(cursor)s) : '');
const r = await fetch(url, {headers: {'X-IG-App-ID': '936619743392459'}, credentials: 'include'});
const t = await r.text();
if (!r.ok || t[0] !== '{') return {ok: false, status: r.status, error: t.slice(0, 160), items: []};
const d = JSON.parse(t);
const items = (d.comments || []).map(c => ({id: String(c.pk), text: c.text || '', likes: c.comment_like_count || 0,
  ts: c.created_at || 0, user: (c.user || {}).username || ''}));
const more = d.next_min_id && (d.has_more_comments || d.has_more_headload_comments);
return {ok: true, items, next: more ? d.next_min_id : null};
""",
    "tiktok": """
const r = await fetch('/api/comment/list/?aid=1988&aweme_id=%(key)s&count=20&cursor=' + (%(cursor)s || 0), {credentials: 'include'});
const t = await r.text();
if (!r.ok || t[0] !== '{') return {ok: false, status: r.status, error: t.slice(0, 160), items: []};
const d = JSON.parse(t);
if (d.status_code && d.status_code !== 0) return {ok: false, status: d.status_code, error: d.status_msg || 'status_code', items: []};
const items = (d.comments || []).map(c => ({id: String(c.cid), text: c.text || '', likes: c.digg_count || 0,
  ts: c.create_time || 0, user: (c.user || {}).unique_id || ''}));
return {ok: true, items, next: (d.has_more && items.length) ? String(d.cursor) : null};
""",
    # First call (cursor null) only finds the comment token on the watch page.
    "youtube": """
function find(o, pred, out) { if (o && typeof o === 'object') { if (pred(o)) out.push(o); for (const k in o) find(o[k], pred, out); } return out; }
let token = %(cursor)s;
if (!token) {
  const w = await fetch('/watch?v=%(key)s', {credentials: 'include'});
  if (!w.ok) return {ok: false, status: w.status, error: 'watch page', items: []};
  const html = await w.text();
  const m = html.match(/var ytInitialData = (\\{.*?\\});<\\/script>/s);
  if (!m) return {ok: false, status: 0, error: 'no ytInitialData on the watch page', items: []};
  for (const s of find(JSON.parse(m[1]), o => o.itemSectionRenderer && o.itemSectionRenderer.sectionIdentifier === 'comment-item-section', [])) {
    const c = find(s, o => o.continuationCommand && o.continuationCommand.token, []);
    if (c.length) { token = c[0].continuationCommand.token; break; }
  }
  return {ok: true, items: [], next: token || null};
}
const r = await fetch('/youtubei/v1/next?prettyPrint=false&key=' + ytcfg.get('INNERTUBE_API_KEY'), {method: 'POST', credentials: 'include',
  headers: {'Content-Type': 'application/json'}, body: JSON.stringify({context: ytcfg.get('INNERTUBE_CONTEXT'), continuation: token})});
if (!r.ok) return {ok: false, status: r.status, error: 'next', items: []};
const j = await r.json();
const items = [];
for (const e of find(j, o => o.commentEntityPayload, []).map(o => o.commentEntityPayload)) {
  const p = e.properties || {}, a = e.author || {}, tb = e.toolbar || {};
  if (p.replyLevel) continue;
  items.push({id: p.commentId, text: (p.content || {}).content || '', likesText: tb.likeCountNotliked || '0',
    when: p.publishedTime || '', user: (a.displayName || '').replace(/^@/, ''), creator: !!a.isCreator});
}
let next = null;
for (const ep of (j.onResponseReceivedEndpoints || [])) {
  const act = ep.appendContinuationItemsAction || ep.reloadContinuationItemsCommand || {};
  for (const it of (act.continuationItems || [])) {
    const t = it.continuationItemRenderer && find(it.continuationItemRenderer, o => o.continuationCommand && o.continuationCommand.token, [])[0];
    if (t) next = t.continuationCommand.token;
  }
}
return {ok: true, items, next};
""",
}
MAX_PAGES = 10


def _read_post(cdp: CDP, platform: str, key: str) -> dict:
    """All pages for one post, one short evaluate each. Returns {ok, status?,
    error?, items}; items read before a failure are kept."""
    items: list[dict] = []
    cursor = None
    for _ in range(MAX_PAGES):
        js = "(async () => {" + _JS_PAGE[platform] % {"key": key, "cursor": json.dumps(cursor)} + "})()"
        try:
            res = cdp.evaluate(js, await_promise=True) or {}
        except Exception as e:  # noqa: BLE001  CDPError, or the socket dropping when Chrome stalls
            return {"ok": False, "status": 0, "error": f"{type(e).__name__}: {str(e)[:140]}", "items": items}
        items.extend(res.get("items") or [])
        if not res.get("ok"):
            return {**res, "items": items}
        cursor = res.get("next")
        if not cursor or len(items) >= PER_POST:
            break
        time.sleep((PAUSE_MS + random.randint(0, 600)) / 1000)
    return {"ok": True, "items": items}


_JS = _JS_PAGE
_PREFIX = {"instagram": "ig", "tiktok": "tt", "youtube": "yt"}


def _load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def _post_key(platform: str, post_id: str) -> str:
    """The id each platform's comment endpoint wants, from our post id."""
    if platform == "instagram":  # ig_<media pk>_<owner id>
        return post_id.split("_")[1]
    return post_id[3:]  # tt_<aweme id>, yt_<video id> (video ids may contain _)


def _compact(s: str) -> int:
    m = re.match(r"\s*([\d.,]+)\s*([KkMm]?)", s or "")
    if not m:
        return 0
    n = float(m.group(1).replace(",", ""))
    return int(n * {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1))


_REL = re.compile(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", re.I)
_DAYS = {"second": 0, "minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30, "year": 365}


def _relative_date(s: str) -> str:
    m = _REL.search(s or "")
    if not m:
        return date.today().isoformat()
    return (date.today() - timedelta(days=int(m.group(1)) * _DAYS[m.group(2).lower()])).isoformat()


def _normalize(platform: str, post_id: str, raw: dict) -> dict | None:
    user = (raw.get("user") or "").strip()
    if not raw.get("id") or not user or user.lower() in OWN or raw.get("creator"):
        return None
    if platform == "youtube":
        likes, day = _compact(raw.get("likesText", "")), _relative_date(raw.get("when", ""))
    else:
        likes = int(raw.get("likes") or 0)
        ts = int(raw.get("ts") or 0)
        day = datetime.fromtimestamp(ts, timezone.utc).date().isoformat() if ts else date.today().isoformat()
    return {
        "id": f"{_PREFIX[platform]}c_{raw['id']}",
        "postId": post_id,
        "platform": platform,
        "username": user,
        "text": raw.get("text") or "",
        "likes": likes,
        "date": day,
    }


def _merge(existing: dict[str, dict], fresh: list[dict]) -> int:
    """Add new comments, refresh likes on known ones. A changed text drops the
    sentiment labels so analyze.py relabels it. A YouTube date stays as first
    seen (relative times drift). Returns how many were new."""
    added = 0
    for c in fresh:
        old = existing.get(c["id"])
        if old is None:
            existing[c["id"]] = c
            added += 1
            continue
        old["likes"] = c["likes"]
        if old.get("text") != c["text"]:
            old["text"] = c["text"]
            for k in ("sentiment", "isQuestion", "sentimentSource", "sentimentV"):
                old.pop(k, None)
    return added


def read(platform: str, full: bool = False, on_progress=None) -> dict:
    """Read comments for one platform. Returns {"posts", "new", "total",
    "pending", "stopped"}. Raises CDPError only when nothing could start."""
    if platform not in _JS:
        return {"posts": 0, "new": 0, "total": 0, "pending": 0, "stopped": "not supported"}
    posts = [p for p in _load(POST_FILES[platform], []) if isinstance(p, dict) and p.get("id")]
    state: dict = _load(STATE_FILE, {})
    todo = [
        p for p in posts
        if int(p.get("comments") or 0) > 0 and (state.get(p["id"]) or {}).get("count") != int(p.get("comments") or 0)
    ]
    todo.sort(key=lambda p: (p.get("date") or "", p.get("time") or ""), reverse=True)
    cap = POSTS_PER_RUN_FULL if full else POSTS_PER_RUN
    batch = todo[:cap]

    all_comments = [c for c in _load(COMMENTS_FILE, []) if isinstance(c, dict) and c.get("id")]
    existing = {c["id"]: c for c in all_comments}
    new_total, done, stopped = 0, 0, ""

    cdp = CDP()
    try:
        if batch:
            cdp.new_tab(PAGE_URLS[platform])
            cdp.wait_for_load(timeout=25)
            time.sleep(4)
        for i, p in enumerate(batch):
            res = _read_post(cdp, platform, _post_key(platform, p["id"]))
            fresh = [c for c in (_normalize(platform, p["id"], r) for r in res.get("items") or []) if c]
            new_total += _merge(existing, fresh)
            if not res.get("ok"):
                stopped = f"stopped at post {i + 1} of {len(batch)}: {res.get('status') or ''} {res.get('error', '')}".strip()
                break
            state[p["id"]] = {"count": int(p.get("comments") or 0), "read": len(fresh), "at": date.today().isoformat()}
            done += 1
            if on_progress:
                on_progress("comments", {"page": i + 1, "totalPosts": len(batch), "newPosts": new_total})
            time.sleep(PAUSE_BETWEEN_POSTS)
    finally:
        cdp.close_owned()
        cdp.detach()
        if done or new_total:
            out = sorted(existing.values(), key=lambda c: (c.get("date") or "", c["id"]), reverse=True)
            COMMENTS_FILE.write_text(json.dumps(out, indent=1, ensure_ascii=False))
            STATE_FILE.write_text(json.dumps(state, indent=1, sort_keys=True))

    return {
        "posts": done,
        "new": new_total,
        "total": sum(1 for c in existing.values() if c.get("platform") == platform),
        "pending": len(todo) - done,
        "stopped": stopped,
    }
