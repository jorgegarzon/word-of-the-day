# Daily run: Word of the Day video

The scheduled task follows these steps every morning (8:40am Mexico City time).
Edit this file to change how the daily run behaves; the task reads it fresh each run.

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
- Caption: first line is a hook, not the definition (e.g. "Finally, a word for every
  family group chat 😂"), then "Guess before the reveal 👀", then 4–5 hashtags:
  `#wordoftheday #vocabulary #englishwords #learnenglish` + one about the topic.
- First comment: a funny example sentence by "us", so the comments aren't empty.

## 5. Send as a DRAFT (never publish directly)
Using the Metricool connector, create a draft/scheduled post for both Instagram (Reel)
and TikTok with the video and caption, scheduled for 10:00am Mexico City time today but
saved as a draft that Jorge approves. If Metricool needs a public video URL, follow the
hosting method recorded in `HOSTING.md`.
If posting fails, still finish steps 6–7 and say what failed.

## 6. Record the word
Append `{"word", "date", "number", "posted": "draft"}` to `words_used.json`, commit
(`Word of the day: <word>`) and push to `main`.

## 7. Tell Jorge
Send a push notification: the word, the hook caption and whether the drafts were created.
Also send the MP4 file into the session.
