#!/usr/bin/env python3
"""Word-of-the-day "guess it" video, 1080x1920 @30fps, ~15s, loops.

Usage: python3 render.py word.json out.mp4 [narration.wav] [--frames]
word.json keys: word, pronunciation, part_of_speech, number, options (3 strings),
answer (0-2), example, captions: [[start, end, text], ...]
"""
import json, math, os, subprocess, sys, wave, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 15.0
GF = "/usr/share/fonts/truetype/google-fonts/"
BOLD, REG, ITAL = GF + "Poppins-Bold.ttf", GF + "Poppins-Regular.ttf", GF + "Poppins-Italic.ttf"
EXTRA = GF + "Poppins-ExtraBold.ttf"
if not os.path.exists(EXTRA): EXTRA = BOLD

CREAM, SOFT, DARK = (255, 248, 236), (215, 205, 240), (30, 20, 55)
GOOD = (88, 214, 141)
# one accent + background pair per day, picked from the word
THEMES = [((255, 196, 61), (28, 22, 64), (92, 40, 120)),
          ((255, 120, 160), (20, 30, 70), (60, 40, 130)),
          ((90, 210, 255), (24, 20, 58), (40, 60, 120)),
          ((170, 255, 120), (18, 34, 52), (30, 80, 100)),
          ((255, 150, 90), (40, 18, 50), (110, 40, 90))]

_f = {}
def F(p, s):
    if (p, s) not in _f: _f[(p, s)] = ImageFont.truetype(p, s)
    return _f[(p, s)]

def clamp(x): return max(0.0, min(1.0, x))
def eo(t): t = clamp(t); return 1 - (1 - t) ** 3
def eb(t):
    t = clamp(t); c = 1.70158; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def win(t, a, b, fin=0.35, fout=0.35):  # visibility 0..1 inside [a,b]
    return min(eo((t - a) / fin), eo((b - t) / fout)) if a <= t <= b else 0.0

class Frame:
    def __init__(self, base): self.img = base
    def el(self, w, h, fn, x, y, alpha=1.0, scale=1.0):
        """draw fn(d, w, h) on a small RGBA tile, paste centered at (x,y)"""
        if alpha <= 0.01: return
        tile = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0)); fn(ImageDraw.Draw(tile), w, h)
        if abs(scale - 1) > 0.005:
            tile = tile.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BICUBIC)
        if alpha < 0.99:
            a = np.asarray(tile.getchannel("A"), dtype=np.float32) * alpha
            tile.putalpha(Image.fromarray(a.astype(np.uint8)))
        self.img.alpha_composite(tile, (int(x - tile.width / 2), int(y - tile.height / 2)))

def ctext(d, w, h, s, f, fill):
    tw = d.textlength(s, font=f); d.text(((w - tw) / 2, (h - f.size * 1.25) / 2), s, font=f, fill=fill)

def fit(s, path, start, maxw):
    while start > 60 and F(path, start).getlength(s) > maxw: start -= 4
    return start

def wrap(s, f, maxw):
    out, cur = [], ""
    for wd in s.split():
        t = (cur + " " + wd).strip()
        if f.getlength(t) <= maxw: cur = t
        else: out.append(cur); cur = wd
    return out + ([cur] if cur else [])

class BG:
    def __init__(self, top, bot):
        y = np.linspace(0, 1, H)[:, None, None]
        self.grad = (np.array(top) * (1 - y) + np.array(bot) * y).repeat(W, 1).astype(np.uint8)
    def __call__(self, t):
        img = Image.fromarray(self.grad).convert("RGBA")
        lay = Image.new("RGBA", (W // 6, H // 6), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        # periods divide DUR so the background loops seamlessly
        for i, (bx, by, r, col, per) in enumerate([(0.2, 0.22, 48, (255, 120, 180, 70), 7.5), (0.8, 0.42, 60, (90, 200, 255, 60), 15),
                                                   (0.3, 0.8, 52, (255, 196, 61, 50), 5), (0.78, 0.86, 40, (160, 255, 200, 45), 7.5)]):
            ph = 2 * math.pi * t / per + i
            x, y = (bx + 0.07 * math.sin(ph)) * W / 6, (by + 0.04 * math.cos(ph)) * H / 6
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18)).resize((W, H), Image.BILINEAR))
        return img

def build(w):
    h = int(hashlib.md5(w["word"].encode()).hexdigest(), 16)
    ACC, top, bot = THEMES[h % len(THEMES)]
    bg = BG(top, bot)
    word = w["word"]; ws = fit(word, EXTRA, 170, W - 140)
    fw = F(EXTRA, ws)
    opts, ans = w["options"], w["answer"]
    fo = F(REG, 50); fol = F(BOLD, 54)
    caps = [] if "--no-captions" in sys.argv else w["captions"]
    # caption chunks: each segment's words, highlighted one at a time
    chunks = []
    for s, e, txt in caps:
        words = txt.split(); n = len(words); step = (e - s) / max(1, n)
        for i in range(0, n, 4):
            grp = words[i:i + 4]
            chunks.append((s + i * step, min(e, s + (i + 4) * step), grp, [s + (i + k) * step for k in range(len(grp))]))

    T_OPT, T_REV, T_EX, T_CTA = 3.4, 7.0, 8.3, 12.6
    WORD_Y, PRON_Y, MID = 640, 790, 1130
    CAP_Y = 1470  # above the bottom ~20% covered by app UI

    def frame(t):
        fr = Frame(bg(t))
        # badge
        fr.el(520, 80, lambda d, a, b: (d.rounded_rectangle([0, 0, a - 1, b - 1], 40, fill=(255, 255, 255, 40)),
              ctext(d, a, b, "WORD OF THE DAY", F(BOLD, 34), ACC)), W / 2, 300)
        # hook line (fades out when options arrive, back in at the very end for the loop)
        hook = 1 - eo((t - (T_OPT - 0.3)) / 0.4) if t < T_OPT + 1 else eo((t - (DUR - 0.55)) / 0.5)
        fr.el(W - 120, 90, lambda d, a, b: ctext(d, a, b, "90% of people can't guess this", F(EXTRA, 62), CREAM), W / 2, 440, hook)
        # the word: always in the same spot, gentle breathing; pop on reveal
        pop = 1 + 0.12 * math.sin(math.pi * clamp((t - T_REV) / 0.45)) if T_REV <= t <= T_REV + 0.45 else 1
        breathe = 1 + 0.015 * math.sin(2 * math.pi * t / 3.75)
        fr.el(W, ws * 1.5, lambda d, a, b: ctext(d, a, b, word, fw, CREAM), W / 2, WORD_Y, 1, breathe * pop)
        fr.el(W, 80, lambda d, a, b: ctext(d, a, b, f"{w['pronunciation']}  ·  {w['part_of_speech']}", F(REG, 44), SOFT), W / 2, PRON_Y)
        # big pulsing "?" filling the middle during the hook (and at the loop point)
        q = hook
        fr.el(400, 400, lambda d, a, b: ctext(d, a, b, "?", F(EXTRA, 300), ACC + (230,)), W / 2, MID - 30, q,
              1 + 0.06 * math.sin(2 * math.pi * t / 1.25))
        # options + countdown
        vis_o = win(t, T_OPT, DUR - 0.5, 0.35, 0.5)
        for i, o in enumerate(opts):
            a_in = eb((t - T_OPT - 0.15 * i) / 0.45)
            is_ans = i == ans; revealed = t >= T_REV
            col = (GOOD + (235,)) if (revealed and is_ans) else (255, 255, 255, 34)
            txtc = DARK if (revealed and is_ans) else CREAM
            dim = (1 - eo((t - T_REV - 0.35) / 0.5)) if (revealed and not is_ans) else 1.0
            lines = wrap(o, fo, 760)
            hh = 70 + 58 * len(lines)
            def draw_opt(d, a, b, i=i, col=col, txtc=txtc, lines=lines):
                d.rounded_rectangle([0, 0, a - 1, b - 1], 34, fill=col)
                d.text((40, b / 2 - fol.size * 0.65), "ABC"[i], font=fol, fill=ACC if col[3] < 100 else DARK)
                for k, ln in enumerate(lines):
                    d.text((115, (b - 58 * len(lines)) / 2 + 58 * k - 6), ln, font=fo, fill=txtc)
            sc = 1.04 if (revealed and is_ans and t < T_REV + 0.6) else 1.0
            oy = 960 + i * 175 - (i * 175 * eo((t - T_REV - 0.75) / 0.5) if is_ans else 0)
            fr.el(920, hh, draw_opt, W / 2 + (1 - a_in) * 300, oy, vis_o * clamp(a_in) * dim, sc)
        if T_OPT + 0.4 <= t < T_REV:
            p = (t - T_OPT - 0.4) / (T_REV - T_OPT - 0.4)
            fr.el(920, 16, lambda d, a, b: (d.rounded_rectangle([0, 0, a - 1, b - 1], 8, fill=(255, 255, 255, 50)),
                  d.rounded_rectangle([0, 0, max(16, (a - 1) * (1 - p)), b - 1], 8, fill=ACC)), W / 2, 870)
        # example
        ex = win(t, T_EX, DUR - 0.5, 0.35, 0.5)
        if ex:
            fi = F(ITAL, 56); lines = wrap("“" + w["example"] + "”", fi, 880)
            def draw_ex(d, a, b):
                d.rounded_rectangle([0, 0, a - 1, b - 1], 40, fill=(255, 255, 255, 30))
                d.text((50, 30), "IN A SENTENCE", font=F(BOLD, 34), fill=ACC)
                for k, ln in enumerate(lines):
                    seg = ln; x = 50; y = 95 + k * 78
                    # highlight the word inside the example
                    low = seg.lower(); j = low.find(word.lower())
                    if j >= 0:
                        pre, mid, post = seg[:j], seg[j:j + len(word)], seg[j + len(word):]
                        d.text((x, y), pre, font=fi, fill=CREAM); x += d.textlength(pre, font=fi)
                        d.text((x, y), mid, font=F(BOLD, 56), fill=ACC); x += d.textlength(mid, font=F(BOLD, 56))
                        d.text((x, y), post, font=fi, fill=CREAM)
                    else: d.text((x, y), seg, font=fi, fill=CREAM)
            fr.el(980, 140 + 78 * len(lines), draw_ex, W / 2, 1215 - (1 - eo((t - T_EX) / 0.5)) * -40, ex)
        # CTA
        cta = win(t, T_CTA, DUR - 0.5, 0.5, 0.5)
        if cta:
            def draw_cta(d, a, b):
                d.rounded_rectangle([0, 0, a - 1, b - 1], 40, fill=ACC)
                ctext(d, a, 84, "Use it in a sentence", F(BOLD, 48), DARK)
                f2 = F(REG, 40); s2 = "in the comments"; tw = d.textlength(s2, font=f2)
                d.text(((a - tw) / 2 - 24, 74), s2, font=f2, fill=DARK)
                ax = (a + tw) / 2 - 6; ay = 96
                d.polygon([(ax, ay), (ax + 32, ay), (ax + 16, ay + 24)], fill=DARK)
            p = eo((t - T_CTA) / 0.5)
            bob = 6 * math.sin(2 * math.pi * (t - T_CTA) * 1.2) if t > T_CTA + 0.5 else 0
            fr.el(700, 145, draw_cta, W / 2, 1450 + (1 - p) * 40 + bob, cta)
        # captions (word-by-word highlight)
        for s, e, grp, starts in chunks:
            if s <= t < e:
                fc = F(EXTRA, 60)
                def draw_cap(d, a, b, grp=grp, starts=starts):
                    widths = [d.textlength(g, font=fc) for g in grp]; sp = d.textlength(" ", font=fc)
                    x = (a - sum(widths) - sp * (len(grp) - 1)) / 2
                    for g, wd, st in zip(grp, widths, starts):
                        active = st <= t
                        col = ACC if (active and (grp.index(g) == len(grp) - 1 or t < starts[grp.index(g) + 1])) else (CREAM if active else (255, 255, 255, 110))
                        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (0, 5)):
                            d.text((x + ox, 10 + oy), g, font=fc, fill=(0, 0, 0, 150))
                        d.text((x, 10), g, font=fc, fill=col); x += wd + sp
                fr.el(W - 80, 100, draw_cap, W / 2, CAP_Y, eo((t - s) / 0.12) if s > 0.05 else 1.0)
        return fr.img
    return frame, bg

EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
def is_emoji(ch): return ord(ch) >= 0x2190 and not ch.isalnum()

def emoji_img(e, size):
    f = ImageFont.truetype(EMOJI, 109); im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), e, font=f, embedded_color=True)
    im = im.crop(im.getbbox() or (0, 0, 1, 1)); r = size / im.height
    return im.resize((max(1, int(im.width * r)), size), Image.LANCZOS)

def rich_lines(s, f, maxw, esize):
    """split hook into text + trailing emoji cluster; wrap the text part"""
    i = len(s)
    while i > 0 and (is_emoji(s[i - 1]) or s[i - 1] in "\ufe0f\u200d "): i -= 1
    txt, emo = s[:i].strip(), s[i:].strip()
    parts = [p + ("." if k < len(txt.split(". ")) - 1 else "") for k, p in enumerate(txt.split(". "))]
    if all(f.getlength(p) <= maxw for p in parts[:-1]) and f.getlength(parts[-1]) <= maxw - esize * 1.2:
        lines = parts
    else: lines = wrap(txt, f, maxw)
    if emo and f.getlength(lines[-1]) + esize * 1.2 > maxw: lines.append("")
    return lines, emo

def build_short(w, dur):
    """Short loop: word + options visible on frame 1, answer revealed at `reveal` s, then the example."""
    h = int(hashlib.md5(w["word"].encode()).hexdigest(), 16)
    ACC, top, bot = THEMES[h % len(THEMES)]
    bg = BG(top, bot)
    word = w["word"]; ws = fit(word, EXTRA, 170, W - 140); fw = F(EXTRA, ws)
    opts, ans = w["options"], w["answer"]
    fo = F(REG, 50); fol = F(BOLD, 54)
    T_REV = float(w.get("reveal", 0.9))
    V3 = bool(w.get("v3"))  # v3: everything on screen at frame 0 with a punch-in, CTA only at the end
    CTA_AT = float(w.get("cta_at", 0.0))
    hook = w.get("screen_hook", ""); hl, emo = [], ""
    for size in range(58, 42, -2):  # shrink until each sentence fits on its own line
        fh = F(EXTRA, size)
        if not hook: break
        hl, emo = rich_lines(hook, fh, W - 120, 64)
        if len(hook.split(". ")) == 1 or hl[0].endswith("."): break
    eim = emoji_img(emo, 64) if emo else None
    def draw_hook(d, a, b):
        for k, ln in enumerate(hl):
            lw = d.textlength(ln, font=fh)
            extra = (eim.width + 16) if (eim and k == len(hl) - 1) else 0
            x = (a - lw - extra) / 2; y = 10 + k * 78
            d.text((x, y), ln, font=fh, fill=CREAM)
            if extra: d._image.alpha_composite(eim, (int(x + lw + 16), int(y + 8)))
    bell = emoji_img("🔔", 48)
    def frame(t):
        fr = Frame(bg(t * 7.5 / dur))
        if hl: fr.el(W - 80, 30 + 78 * len(hl), draw_hook, W / 2, 220 + 39 * (len(hl) - 1))
        fc = F(ITAL, 50); cta = w.get("cta", "Follow for your word of the day")
        def draw_cta(d, a, b):
            tw = d.textlength(cta, font=fc); x = (a - tw - bell.width - 14) / 2; y = (b - fc.size * 1.25) / 2
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (0, 4)):
                d.text((x + ox, y + oy), cta, font=fc, fill=(0, 0, 0, 140))
            d.text((x, y), cta, font=fc, fill=(255, 255, 255, 255))
            d._image.alpha_composite(bell, (int(x + tw + 14), int((b - bell.height) / 2)))
        cta_a = (eo((t - CTA_AT) / 0.3) if t >= CTA_AT else 0.0) if V3 else 1.0
        fr.el(980, 90, draw_cta, W / 2, 1545, cta_a)
        pop = 1 + 0.10 * math.sin(math.pi * clamp((t - T_REV) / 0.3)) if T_REV <= t <= T_REV + 0.3 else 1
        if V3 and t < 0.3: pop = 0.86 + 0.14 * eo(t / 0.3)  # grow in (shrinking from >1 would clip long words)
        fr.el(W, ws * 1.5, lambda d, a, b: ctext(d, a, b, word, fw, CREAM), W / 2, 520, 1, pop)
        fr.el(W, 80, lambda d, a, b: ctext(d, a, b, f"{w['pronunciation']}  ·  {w['part_of_speech']}", F(REG, 44), SOFT), W / 2, 670)
        revealed = t >= T_REV
        OPT_AT = w.get("options_at", [0.4, 0.8, 1.2]); CNT_AT = w.get("countdown_at", [1.4, 1.6, 1.8])
        for k, c0 in enumerate(CNT_AT):
            c1 = CNT_AT[k + 1] if k + 1 < len(CNT_AT) else min(T_REV, c0 + (CNT_AT[1] - CNT_AT[0] if len(CNT_AT) > 1 else 0.5))
            if c0 <= t < c1:
                fr.el(300, 300, lambda d, a, b, k=k: ctext(d, a, b, str(len(CNT_AT) - k), F(EXTRA, 220), ACC),
                      W / 2, 1400, 1, max(0.01, eb((t - c0) / 0.15)))
        for i, o in enumerate(opts):
            if t < OPT_AT[i]: continue
            is_ans = i == ans
            col = (GOOD + (235,)) if (revealed and is_ans) else (255, 255, 255, 34)
            txtc = DARK if (revealed and is_ans) else CREAM
            dim = (1 - 0.7 * eo((t - T_REV) / 0.2)) if (revealed and not is_ans) else 1.0
            lines = wrap(o, fo, 760); hh = 70 + 58 * len(lines)
            def draw_opt(d, a, b, i=i, col=col, txtc=txtc, lines=lines):
                d.rounded_rectangle([0, 0, a - 1, b - 1], 34, fill=col)
                d.text((40, b / 2 - fol.size * 0.65), "ABC"[i], font=fol, fill=ACC if col[3] < 100 else DARK)
                for k, ln in enumerate(lines):
                    d.text((115, (b - 58 * len(lines)) / 2 + 58 * k - 6), ln, font=fo, fill=txtc)
            sc = 1 + 0.08 * math.sin(math.pi * clamp((t - T_REV) / 0.3)) if (revealed and is_ans) else max(0.01, eb((t - OPT_AT[i]) / 0.2))
            if V3 and not revealed: sc = 1 + 0.10 * (1 - eo((t - 0.05 * i) / 0.3))
            fr.el(920, hh, draw_opt, W / 2, 840 + i * 175, dim, sc)
        T_EX = float(w.get("sentence_at", T_REV + 0.1))
        ex = eo((t - T_EX) / 0.2) if t >= T_EX else 0
        if ex:
            for es in (50, 46, 42):
                fi = F(ITAL, es); fb = F(BOLD, es); lines = wrap("“" + w["example"] + "”", fi, 900)
                if len(lines) <= 2: break
            def draw_ex(d, a, b):
                d.rounded_rectangle([0, 0, a - 1, b - 1], 36, fill=(255, 255, 255, 30))
                for k, ln in enumerate(lines):
                    x = (a - d.textlength(ln, font=fi)) / 2; y = 28 + k * 68 * fi.size / 50
                    j = ln.lower().find(word.lower())
                    if j >= 0:
                        pre, mid, post = ln[:j], ln[j:j + len(word)], ln[j + len(word):]
                        d.text((x, y), pre, font=fi, fill=CREAM); x += d.textlength(pre, font=fi)
                        d.text((x, y), mid, font=fb, fill=ACC); x += d.textlength(mid, font=fb)
                        d.text((x, y), post, font=fi, fill=CREAM)
                    else: d.text((x, y), ln, font=fi, fill=CREAM)
            hb = 56 + 68 * len(lines)
            fr.el(980, hb, draw_ex, W / 2, 1280 + hb / 2 + (1 - ex) * 30, ex)
        return fr.img
    return frame, bg

def make_music(dur, path, sr=44100, fade_in=True):
    t = np.arange(int(dur * sr)) / sr; out = np.zeros_like(t)
    chords = [[261.63, 329.63, 392.0, 493.88], [220.0, 261.63, 329.63, 392.0], [174.61, 220.0, 261.63, 329.63], [196.0, 246.94, 293.66, 392.0]]
    clen = dur / 4
    for ci in range(4):
        ch = chords[ci]; s = ci * clen
        for f in ch:  # pads crossfade so the loop point is smooth
            env = np.clip(1 - np.abs((t - s - clen / 2) / (clen * 0.75)), 0, 1)
            out += env * 0.05 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t))
        for k in range(int(clen / 0.4)):
            ps = s + k * 0.4; f = ch[k % 4] * 2; m = (t >= ps) & (t < ps + 1.2); pt = t[m] - ps
            out[m] += 0.055 * np.exp(-pt * 5) * np.sin(2 * np.pi * f * pt)
    d = int(0.3 * sr); echo = np.zeros_like(out); echo[d:] = out[:-d] * 0.3; out += echo
    out *= np.minimum(1, np.minimum(t / 0.3 if fade_in else 1, (dur - t) / 0.4))
    out = out / (np.abs(out).max() + 1e-9) * 0.5
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((np.stack([out, out], 1) * 32767).astype(np.int16).tobytes())

def add_ticks(path, times, sr=44100):
    """mix a short clock tick into the music at each time (countdown)"""
    with wave.open(path) as wf: a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32767
    tt = np.arange(int(0.06 * sr)) / sr
    tick = (np.sin(2 * np.pi * 1900 * tt) * 0.6 + np.sin(2 * np.pi * 950 * tt) * 0.4) * np.exp(-tt * 90) * 0.55
    for t0 in times:
        i = int(t0 * sr); n = min(len(tick), len(a) - i)
        if n > 0: a[i:i + n] += tick[:n, None]
    a = np.clip(a, -1, 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes((a * 32767).astype(np.int16).tobytes())

def add_pop(path, sr=44100):
    """v3: a bright pop at 0.0s so the first frame isn't silent"""
    with wave.open(path) as wf: a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32767
    tt = np.arange(int(0.18 * sr)) / sr
    f = 1400 * np.exp(-tt * 12) + 380  # quick downward sweep
    pop = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 22) * 0.7
    a[:len(pop)] += pop[:, None]; a = np.clip(a, -1, 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes((a * 32767).astype(np.int16).tobytes())

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    w = json.load(open(args[0])); out = args[1]; narr = args[2] if len(args) > 2 else None
    work = os.path.join(os.path.dirname(os.path.abspath(out)), "_work"); os.makedirs(work, exist_ok=True)
    global DUR
    if "--short" in sys.argv:
        DUR = float(w.get("duration", 2.0)); frame, bg = build_short(w, DUR)
        times = [0.0, 0.15, 1.0, 2.0, float(w.get("reveal", 0.9)) + 0.4, DUR - 0.1] if w.get("v3") else [0.3, 2.0, 2.7, 4.3, 5.0, DUR - 0.1]
    else:
        frame, bg = build(w); times = [0.0, 2.0, 5.5, 7.6, 10.5, 13.8, 14.97]
    if "--frames" in sys.argv:
        for i, ts in enumerate(times):
            frame(ts).convert("RGB").save(f"{work}/f{i}.jpg", quality=88)
        return
    n = int(DUR * FPS); vid = f"{work}/video.part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    for k in range(n): p.stdin.write(frame(k / FPS).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait(): raise SystemExit("video encode failed")
    os.replace(vid, f"{work}/video.mp4")
    make_music(DUR, f"{work}/music.wav", fade_in=not w.get("v3"))
    if "--short" in sys.argv: add_ticks(f"{work}/music.wav", w.get("countdown_at", [1.4, 1.6, 1.8]))
    if w.get("v3"): add_pop(f"{work}/music.wav")
    tmp = out[:-4] + ".part.mp4"
    if narr:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/video.mp4", "-i", f"{work}/music.wav", "-i", narr,
               "-filter_complex", "[1:a]volume=0.3[m];[2:a]volume=1.4[n];[m][n]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "0:v", "-map", "[a]"]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/video.mp4", "-i", f"{work}/music.wav", "-map", "0:v", "-map", "1:a"]
    subprocess.run(cmd + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)

if __name__ == "__main__":
    main()
