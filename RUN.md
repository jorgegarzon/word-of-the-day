# Daily run: Word of the Day video (@canyouguessthisword)

The scheduled task follows these steps every morning (starts 5:39am New York time; the post goes
live at 6:00am New York time). Fully automated: no human approval step.
Edit this file to change how the daily run behaves; the task reads it fresh each run.
All dates (file names, `words_used.json`) use Mexico City local time: `TZ=America/Mexico_City date +%F`.

## 1. Pick the word
- Read `words_used.json`. Never reuse a word that is in it.
- Choose a fun, real English word that people can use in everyday life: one that names a
  feeling, a situation or a behavior almost everyone has run into (e.g. *kerfuffle*,
  *petrichor*, *defenestration*, *ultracrepidarian*, *lollygag*, *snollygoster*).
  Avoid technical jargon, offensive words and words with sexual meanings.
- Verify the meaning, part of speech and pronunciation with web search against at least one
  real dictionary (Merriam-Webster, Cambridge, Oxford Learner's, Collins). If sources
  disagree or the word can't be verified, pick another word.

## 2. Write `out/word.json`
Same shape as `examples/kerfuffle.json`:
- `word` lowercase; `pronunciation` in simple respelling like `ker-FUFF-ul` (no IPA);
  `part_of_speech`; `number` = number of posted entries in `words_used.json` + 1.
- `options`: exactly 3, each at most ~28 characters so it fits on one line.
  One is the real meaning in plain words; two are believable but clearly wrong (ideally
  ones the word *sounds* like it could mean). Put the correct one at a random position
  and set `answer` to its index (0, 1 or 2).
- `example`: one funny, relatable sentence of at most ~70 characters that uses the word.
- `captions`: keep the same 5 timing slots as the example, rewritten for today's word
  (not shown in the current no-caption design, kept for when a narrator is added).

## 3. Render and check
```
python3 render.py out/word.json out/preview.mp4 --no-captions --frames
python3 render.py out/word.json out/wotd-YYYY-MM-DD.mp4 --no-captions
```
Look at the preview frames in `out/_work/` before the full render. Text must not
overflow its box or run off screen; if it does, shorten the text and redraw.
Confirm the final file is 15.0 seconds with `ffprobe`.

## 4. Caption and first comment
Format (never reveal the meaning in the caption; people read it while the video plays):
```
<hook>

Guess before the reveal 👀 A, B or C?

Follow @canyouguessthisword for tomorrow's word

#wordoftheday #vocabulary #englishwords #learnenglish #<topic>
```
**Hook styles** (record which one you used):
- `relatable`: a moment everyone has lived. "When your boss says 'can we talk?' 😬"
- `challenge`: dares the viewer. "I bet you've felt this and didn't know the word"
- `tag`: invites tagging. "Tag the friend who gets this before every flight ✈️"
- `surprise`: the word sounds fake. "This sounds made up. It's not."

**Choosing the style** (see `metrics.json`, written in step 6b):
1. Post #1 uses `relatable`. After that, rotate in the order relatable → challenge → tag →
   surprise, continuing from the last style in `words_used.json`.
2. Once every style has at least 4 posts with metrics, switch to: 60% of days the style with the
   best average score, 40% of days rotate through the others (keep testing; tastes change).
3. Score per post = (comments + shares + saves) per 1,000 views, plus 0.5 × views/1,000.
   Ignore posts younger than 3 days (numbers still moving).

First comment: a funny sentence using the word "from us", so the comments aren't empty.

## 5. Deliver
- Copy the final video to `videos/wotd-YYYY-MM-DD-<word>.mp4` (this folder is the archive).
- **Publish through Metricool (automatic, no draft).** Do step 6 (commit and push) first, so the
  video is reachable at its raw GitHub URL
  (`https://raw.githubusercontent.com/jorgegarzon/word-of-the-day/main/videos/<file>`; the repo must
  be public, otherwise report it and stop). Then call `getBrandSettings` and create ONE scheduled
  post with `createScheduledPost` for **every network connected to the brand** (today only
  Instagram; add TikTok, YouTube Shorts, Facebook Reels etc. as they appear), with
  `"draft": false` and `"autoPublish": true`, so Metricool publishes it by itself:
  - date: 06:00 America/New_York today; if that is less than 5 minutes away or already past,
    10 minutes from now.
  - Instagram: `instagramData.type = "REEL"`, `showReelOnFeed: true`. TikTok: `tiktokData` with
    `privacyOption: "PUBLIC_TO_EVERYONE"`. YouTube: type `short`, `madeForKids: false`, title =
    "<Word>: can you guess what it means? #shorts".
  - text = the caption, `firstCommentText` = the first comment.
  Then record the returned post id/uuid and `plannerUrl` in `words_used.json`
  (`"posted": "scheduled"`, `"metricool_uuid"`, `"publish_at"`) and push again.
  If Metricool rejects the post, report the exact error (email + push) and stop; do not retry
  with different content.
- **Always:** send the MP4 into this session with SendUserFile, and send a push notification:
  today's word, the publish time and the networks, or what failed.

## 6. Record the word
Append `{"word", "date", "number", "posted": "scheduled" (or "failed"), "hook_style", "hook", "caption"}`
to `words_used.json`,
then commit (`Word of the day: <word>`) and push to `main`.

## 6b. Measure
Measurement runs separately every evening (see `MEASURE.md`); the morning run does not measure.

## 7. Email Jorge
With the Microsoft 365 connector, send ONE email to jorgeogarzon@live.com:
- Subject: `Word of the day: <word>`
- Body (HTML): the caption ready to copy, the first comment, the 3 options with the answer,
  a link to the video in GitHub
  (`https://github.com/jorgegarzon/word-of-the-day/blob/main/videos/<file>`),
  the publish time, the networks and the Metricool planner link, and anything that failed.
- The weekly hook report is sent by the nightly measurement run (`MEASURE.md`).
