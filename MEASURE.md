# Nightly run: measure Word of the Day performance

A separate scheduled task runs this every night (11:40pm New York time).

1. Check publishing: for every entry in `words_used.json` with `"posted": "scheduled"` whose
   `publish_at` has passed, confirm in Metricool that it went live (it no longer appears in
   `getScheduledPosts`, and it shows up in Instagram posts/reels analytics). Set `"posted"` to
   `"published"`, or to `"failed"` with the reason, and alert Jorge (push + email) on any failure.
2. Measure: for every published post up to 30 days old, fetch its stats from Metricool with
   `getAnalyticsDataByMetrics` (use `getAnalyticsAvailableMetrics` for Instagram `reels` and, when
   connected, TikTok `posts` to find the metric IDs): views/plays, reach, likes, comments, shares,
   saves, follows, average watch time when available. Match posts by publish date and caption.
   Write/refresh its entry in `metrics.json`:
   `{"word", "date", "hook_style", "instagram": {...}, "tiktok": {...}, "score", "age_days", "updated"}`.
   Score = (comments + shares + saves) per 1,000 views + 0.5 × views/1,000. Posts younger than
   3 days get a score but are marked `"provisional": true` and RUN.md ignores them for hook choice.
3. Commit `metrics.json` and `words_used.json` (`Metrics: <date>`) and push to `main`.
4. Notify only when it matters: push + email if a post failed to publish, or a post has
   2× the average score of the others (a hit worth copying). Otherwise stay quiet.
   On Sunday nights, email jorgeogarzon@live.com (Microsoft 365 connector) a weekly "Hook report":
   per hook style the posts measured, average views and score, the leader, and the 3 best and
   3 worst posts of the past 4 weeks with their hooks; say when there isn't enough data yet.
