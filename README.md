# Word of the Day

Daily 15-second vertical (1080×1920) "guess the meaning" video for Instagram Reels and TikTok.

- `render.py`: draws the video (Python + Pillow + numpy + ffmpeg). Music is synthesized; no assets needed.
- `RUN.md`: the steps the daily scheduled task follows.
- `words_used.json`: every word already used, so none repeat.
- `examples/kerfuffle.json`: the input format.

Try it locally: `python3 render.py examples/kerfuffle.json out.mp4 --no-captions`
