#!/usr/bin/env python3
# v2 of the Nov 20 - Dec 31 2026 batch (decided 2026-11-19, see docs/2026-11-19-v2-rerender.md).
# Same words, options, answers, examples and first comments as batch/2026-nov-dec.py.
# Changes: 6.6s short loop format (render.py --short), ~2/3 "surprise" hooks with an emoji,
# hook shown on screen, weekends at 12:00 MST (13:00 Mexico City), weekdays stay 10:00 Mexico City.
# Usage: python3 batch/2026-nov-dec-v2.py <old_batch.json> <out.json>
import json, sys, datetime
S, R, C, T = "surprise", "relatable", "challenge", "tag"
HOOKS = {
"nincompoop": (S, "This sounds like baby talk. It's a real word 🍼"),
"rigmarole": (R, "When you just wanted to cancel a subscription 😩"),
"hornswoggle": (S, "This sounds like a farm animal. It's not 🐄"),
"hobnob": (S, "This sounds like something hobbits do. It's not 🧙"),
"higgledy-piggledy": (C, "I bet your bedroom looks like this right now 👀"),
"mollycoddle": (S, "This sounds like a way to cook eggs. It's not 🥚"),
"gobsmacked": (S, "This sounds like a punch. It's not 🥊"),
"fuddy-duddy": (T, "Tag the friend who still prints their boarding pass 🎫"),
"bumbershoot": (S, "This sounds like a clown's cannon. It's not 🤡"),
"flibbertigibbet": (S, "This sounds like a goblin. It's not 👺"),
"curmudgeon": (R, "When someone hates every new song on the radio 📻"),
"schadenfreude": (S, "This sounds like a German dessert. It's not 🍰"),
"serendipity": (S, "This sounds like a party dip. It's not 🥣"),
"quidnunc": (C, "Bet you know someone exactly like this 👀"),
"balderdash": (S, "This sounds like a race for bald guys. It's not 🏃"),
"doppelganger": (S, "This sounds like a monster. It's not 👹"),
"grandiloquent": (T, "Tag the friend whose toasts last 20 minutes 🥂"),
"cacophony": (S, "This sounds like a bad cough. It's not 😷"),
"wanderlust": (S, "This sounds like a romance novel. It's not 💘"),
"kvetch": (R, "When your uncle starts talking about the weather 🌧️"),
"schlep": (S, "This sounds like slurping soup. It's not 🍜"),
"hoodwink": (S, "This sounds like a flirty wink. It's not 😉"),
"hubbub": (C, "Bet you've been in one of these this week 👀"),
"flummoxed": (S, "This sounds like a sneeze. It's not 🤧"),
"zhuzh": (S, "This sounds like a bee. It's not 🐝"),
"copacetic": (T, "Tag the friend who says 'all good' when it's not 😅"),
"humdinger": (S, "This sounds like a doorbell. It's not 🔔"),
"codswallop": (S, "This sounds like a fish slap. It's not 🐟"),
"gumption": (R, "When you finally ask for that raise 💪"),
"chutzpah": (S, "This sounds like a spicy sauce. It's not 🌶️"),
"finagle": (S, "This sounds like a dramatic finale. It's not 🎭"),
"boondoggle": (C, "Bet your office has one of these right now 👀"),
"bloviate": (S, "This sounds like a sea creature. It's not 🐡"),
"sesquipedalian": (S, "This sounds like a bug with 100 legs. It's not 🐛"),
"borborygmus": (T, "Tag the friend whose stomach does this in meetings 🔊"),
"phosphene": (S, "This sounds like a glowing fish. It's not 🐠"),
"gloaming": (S, "This sounds gloomy. It's actually beautiful 🌆"),
"brouhaha": (R, "When someone takes the last slice at the family party 🍕"),
"ragamuffin": (S, "This sounds like a muffin. It's not 🧁"),
"skulduggery": (S, "This sounds like digging up skulls. It's not 💀"),
"tomfoolery": (C, "Bet you did this as a kid 😏"),
"hullabaloo": (S, "This sounds like a hula dance. It's not 🌺"),
}
TIMING = dict(duration=6.6, options_at=[0.6, 1.2, 1.8], countdown_at=[2.4, 3.0, 3.6],
              reveal=4.2, sentence_at=4.6, cta="Follow for your word of the day")
old = {o["json"]["word"]: o for o in json.load(open(sys.argv[1]))}
out = []
for word, (style, hook) in HOOKS.items():
    o = old[word]; d = datetime.date.fromisoformat(o["date"])
    tag = o["caption"].rsplit("#", 1)[1]
    cap = f"{hook}\n\nGuess before the reveal 👀 A, B or C?\n\nFollow @canyouguessthisword for tomorrow's word\n\n#wordoftheday #vocabulary #englishwords #learnenglish #{tag}"
    weekend = d.weekday() >= 5
    j = dict(o["json"]); j.update(TIMING); j["screen_hook"] = hook
    out.append({"date": o["date"], "hook_style": style, "hook": hook, "caption": cap,
                "first_comment": o["first_comment"], "weekend": weekend,
                "publish_local": f"{o['date']}T{'13' if weekend else '10'}:00:00",  # America/Mexico_City
                "publish_at": f"{o['date']}T{'13' if weekend else '10'}:00:00-06:00", "json": j})
assert len(out) == 42 and out[0]["date"] == "2026-11-20" and out[-1]["date"] == "2026-12-31"
json.dump(out, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
from collections import Counter
print(len(out), Counter(o["hook_style"] for o in out), sum(o["weekend"] for o in out), "weekend")
