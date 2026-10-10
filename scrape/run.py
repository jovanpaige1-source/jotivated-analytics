#!/usr/bin/env python3
"""
Creator Dashboard scrape runner, a command line tool with no server.

Incremental, all platforms:
    python3 scrape/run.py
Only some platforms:
    python3 scrape/run.py --platforms instagram,tiktok
Master sweep, re-page everything:
    python3 scrape/run.py --full
Skip the analytics and vault rebuild:
    python3 scrape/run.py --no-analyze
Just rebuild the derived JSON:
    python3 scrape/run.py --analyze-only

Talks to the dashboard Chrome window from setup guide Part D1
(CHROME_CDP_PORT, default 9222), which carries your logins. It opens its own
tabs and closes them on every exit path.

Exit codes:
    0  every requested platform scraped
    1  some platforms failed (others succeeded, derived files rebuilt)
    2  every platform failed, or refused to start (Chrome not reachable)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Progress lines should appear live even when piped to tee / a log file.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

from scrape import analyze  # noqa: E402
from scrape.cdp import CDP, CDPError, default_port  # noqa: E402
from scrape.platforms import studio  # noqa: E402
from scrape.server import (  # noqa: E402
    PLATFORM_RUNNERS,
    PLATFORMS,
    load_scrape_state,
    record_platform_result,
    save_scrape_state,
)

# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platforms", default=",".join(PLATFORMS), help="comma-separated subset")
    ap.add_argument("--full", action="store_true", help="master sweep: ignore incremental early-stop")
    ap.add_argument("--no-analyze", action="store_true", help="skip rebuilding analytics/vault/history")
    ap.add_argument("--analyze-only", action="store_true", help="only rebuild derived JSON, no scraping")
    ap.add_argument("--quiet", action="store_true", help="suppress per-page progress lines")
    ap.add_argument("--no-studio", action="store_true",
                    help="skip the TikTok Studio and YouTube Studio pass that fills likes, comments and shares")
    args = ap.parse_args()

    if args.analyze_only:
        summary = analyze.run()
        print(f"analyze: {summary}")
        return 0

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    bad = [p for p in platforms if p not in PLATFORM_RUNNERS]
    if bad:
        print(f"unknown platform(s): {', '.join(bad)}", file=sys.stderr)
        return 2

    # Fail fast if Chrome is not reachable.
    try:
        CDP().list_tabs()
    except CDPError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2

    mode = "FULL SWEEP" if args.full else "incremental"
    print(f"scrape [{mode}] on Chrome :{default_port()} -> {', '.join(platforms)}")

    state = load_scrape_state()
    errors: dict[str, str] = {}
    results: dict[str, dict] = {}
    t0 = time.time()

    for platform in platforms:
        runner = PLATFORM_RUNNERS[platform]
        started = time.time()

        def progress(stage: str, info: dict, _p=platform) -> None:
            if not args.quiet:
                brief = ", ".join(f"{k}={v}" for k, v in info.items() if k in (
                    "page", "round", "newPosts", "totalPosts", "consecutiveKnown", "reason"
                ))
                print(f"  [{_p}] {stage} {brief}")

        try:
            result = runner(on_progress=progress, full=args.full)
            record_platform_result(state, platform, result)
            save_scrape_state(state)
            results[platform] = result
            print(
                f"  {platform}: +{result.get('newPosts', 0)} new, "
                f"{result.get('totalScraped', 0)} total"
                f"{', stopped early' if result.get('stoppedEarly') else ''}"
                f"{', followers ' + str(result['followers']) if result.get('followers') else ''}"
                f"  ({time.time() - started:.0f}s)"
            )
            # The public page gives views only for these two; the signed-in
            # studio gives the rest. A studio failure (not signed in, layout
            # change) is reported but never undoes the base reader's result.
            if platform in studio.ENRICHERS and not args.no_studio:
                try:
                    stats = studio.ENRICHERS[platform](on_progress=progress)
                    result["studio"] = stats
                    print(f"  {platform} studio: {stats['matched']} posts matched, {stats['changed']} updated")
                except (CDPError, Exception) as e:  # noqa: BLE001
                    result["studioError"] = str(e)
                    print(f"  {platform} studio: SKIPPED {str(e)[:160]}", file=sys.stderr)
        except CDPError as e:
            errors[platform] = str(e)
            sub = state.get(platform, {}) or {}
            sub["status"] = "error"
            sub["lastError"] = str(e)
            state[platform] = sub
            save_scrape_state(state)
            print(f"  {platform}: FAILED {e}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            errors[platform] = f"{type(e).__name__}: {e}"
            print(f"  {platform}: FAILED {type(e).__name__}: {e}", file=sys.stderr)

    if results and not args.no_analyze:
        summary = analyze.run()
        print(f"analyze: {summary}")

    print(f"done in {time.time() - t0:.0f}s: {len(results)} ok, {len(errors)} failed")
    if errors and not results:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
