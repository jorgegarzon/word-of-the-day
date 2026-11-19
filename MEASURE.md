# Nightly run: measure Word of the Day performance

A separate scheduled task runs this every night (11:40pm New York time).
Background on the metrics and the v2 format: `docs/2026-11-19-v2-rerender.md`.

1. Check publishing: for every entry in `words_used.json` with `"posted": "scheduled"` whose
   `publish_at` has passed, confirm in Metricool that it went live (`getScheduledPosts` shows both
   providers `PUBLISHED` with a public URL, and it shows up in Instagram reels analytics). Set `"posted"`
   to `"published"` and add `instagram_url`, `facebook_url` and `published_at`, or set it to `"failed"` with
   the reason, and alert Jorge (push + email) on any failure.

2. Measure each post: for every published post up to 30 days old, fetch its stats with
   `getAnalyticsDataByMetrics` (brand 7951497). Match posts by URL, or by publish date and caption.
   - Instagram reels: IGRE02 date, IGRE06 url, IGRE23 views, IGRE11 reach, IGRE10 likes, IGRE07 comments,
     IGRE21 shares, IGRE12 saves, IGRE24 avg watch time, **IGRE30 skip rate** (% who swiped away within
     3s), **IGRE28 view rate** (% who watched more than 3s).
   - Facebook reels: FBRE02, FBRE06, FBRE10 views, FBRE11 reach, FBRE08 likes, FBRE13 avg watch time.
   - TikTok, when connected: use `getAnalyticsAvailableMetrics` (network tiktok, connector posts).

   Write/refresh its entry in `metrics.json`:
   `{"word", "date", "hook_style", "format", "instagram": {..., "skip_rate", "view_rate"}, "facebook": {...},
   "tiktok": {...}, "score", "provisional", "low_sample", "age_days", "updated"}`.
   `format` comes from `words_used.json` (`"v2-6.6s"`, or `"v1-15s"` when the entry has none).

   **Engagement**: we post the first comment on every reel ourselves, so subtract 1 from Instagram
   comments: `comments_ext = max(0, comments - 1)`, and store it next to `comments`.

   **Score** = 1,000 × (likes + comments_ext + shares + saves) / views + views / 100,
   using Instagram only. (Engagement per 1,000 views, plus 1 point per 100 views, so reach counts and
   one like on a reel with 20 views can't win by itself.)
   - `"provisional": true` if the post is younger than 3 days.
   - `"low_sample": true` if Instagram views < 50.
   - Provisional or low-sample posts get a score, but RUN.md hook choice, hit alerts and best/worst
     lists ignore them.

3. Followers: append today's line to `followers.json` (create it if missing), one entry per date,
   replacing that date's entry if it already exists:
   `{"date", "instagram_followers"}` from IGEV01 (Instagram evolution, for that date), and
   `"instagram_gained"` and `"instagram_lost"` from IGEV43 and IGEV44 when Metricool returns them.
   Facebook page followers too if a metric is available. Metricool has no per-reel follows, so link
   follower changes to posts by date only.

4. Commit `metrics.json`, `words_used.json` and `followers.json` (`Metrics: <date>`) and push to `main`.

5. Notify only when it matters (push + email to jorgeogarzon@live.com via the Microsoft 365 connector):
   - A post failed to publish.
   - A hit: a non-provisional, non-low-sample post whose score is ≥ 2× the average of the other eligible
     posts **and** whose Instagram views are above the median of the eligible posts.
   - Otherwise stay quiet.

   **Sunday nights**: email a weekly "Hook report":
   - Per hook style: posts measured, avg views, avg skip rate, avg watch time, avg score; name the leader.
   - **v1 vs v2**: for each format, posts measured, avg views, avg skip rate, avg view rate, avg watch time,
     and followers gained during the days each format was posting (from `followers.json`).
   - The 3 best and 3 worst eligible posts of the past 4 weeks, with their hooks.
   - Followers at the start and end of the week.
   - Say when there isn't enough data yet (fewer than 4 eligible posts in a group).
