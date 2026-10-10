"""Account handles per platform. Edit these before the first scrape.

Instagram, TikTok and Threads: the username without the @.
YouTube: the handle with the @, plus the channel ID below (Settings, Channel,
Advanced settings in YouTube Studio). YouTube is scraped by channel ID so a
handle rename cannot break it; the handle is used for display and links.
LinkedIn: the last part of the profile address, linkedin.com/in/<this-part>.
"""

HANDLES = {
    "instagram": "notyo_averagejo",
    "tiktok": "notyo_averagejo",
    "youtube": "@notyo_averagejo",
    "threads": "your.threads.username",
    "linkedin": "your-linkedin-slug",
}

# Stable identifiers that survive handle renames.
YOUTUBE_CHANNEL_ID = "UCjz0bqe7SN8DSGFlYG2IiCQ"  # required: 24 characters starting with UC
INSTAGRAM_USER_ID = ""  # optional, informational

# Platforms this dashboard reads and shows. `python3 scrape/run.py` with no --platforms
# pulls exactly these. To add Threads or LinkedIn later: put the handle above, add it
# here, and add it to PLATFORMS in lib/derive.ts so the dashboard shows it.
ENABLED = ["instagram", "tiktok", "youtube"]
