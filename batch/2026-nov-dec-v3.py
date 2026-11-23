#!/usr/bin/env python3
# v3 A/B test for Nov 24 - Dec 31 2026 (decided 2026-11-23, see docs/2026-11-23-v3-ab-test.md).
# Input: the v2 batch json (batch/2026-nov-dec-v2.py output). Every other post from Nov 24 becomes v3,
# starting with Nov 24; the rest stay v2 (same video, unchanged). Words, options, answers, examples,
# captions, first comments, hooks (in the caption) and publish times are unchanged.
# v3 changes (fix the ~50% drop at the 1-second mark):
#   - word, question and all 3 options are on screen at frame 0, with a punch-in animation
#   - on-screen text is a direct question; the hook moves to the caption only
#   - countdown starts at 0.6s, reveal at 3.0s, 5.4s loop
#   - a pop sound at 0.0s, no audio fade-in
#   - "Follow for your word of the day" only appears at the end (with the example)
# Usage: python3 batch/2026-nov-dec-v3.py <v2.json> <out.json>
import json, sys, datetime
V3_TIMING = dict(v3=True, duration=5.4, options_at=[0.0, 0.0, 0.0], countdown_at=[0.6, 1.4, 2.2],
                 reveal=3.0, sentence_at=3.3, cta_at=3.3, cta="Follow for your word of the day",
                 screen_hook="What does this word mean? 🤔")
START = datetime.date(2026, 11, 24)
out = []
for o in json.load(open(sys.argv[1])):
    d = datetime.date.fromisoformat(o["date"])
    if d < START: continue
    o = dict(o)
    if (d - START).days % 2 == 0:
        o["format"] = "v3-5.4s"; j = dict(o["json"]); j.update(V3_TIMING); o["json"] = j
    else:
        o["format"] = "v2-6.6s"
    out.append(o)
assert out[0]["date"] == "2026-11-24" and out[0]["format"] == "v3-5.4s" and out[-1]["date"] == "2026-12-31"
json.dump(out, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
from collections import Counter
print(len(out), Counter(o["format"] for o in out), Counter((o["format"], o["hook_style"]) for o in out),
      Counter((o["format"], o["weekend"]) for o in out))
