# Nobody Told Larry — posting & stats automation

Runs free on GitHub Actions.

- **post** (every 30 min): publishes episodes in `queue.json` whose `publish_at` has arrived — Facebook Reel + Instagram Reel at that time, YouTube uploaded up to 48h early with a native schedule. Set a platform to `"queued"` to have it posted; the bot writes back `"done"` or `"failed"` (+ error).
- **stats** (daily ~10 AM ET): appends views/likes/comments/shares/saves per post to `stats.csv`.
- **weekly** (Mondays ~11:40 AM ET): Claude Haiku reads the last 14 days of stats and opens a GitHub issue with the ranking + next-episode advice (GitHub emails it to you). Costs about a cent.
- TikTok is posted through Higgsfield (TikTok requires a manual tap on the post card).

## Secrets (Settings → Secrets and variables → Actions)
META_PAGE_TOKEN, META_PAGE_ID, IG_USER_ID, YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, ANTHROPIC_API_KEY
