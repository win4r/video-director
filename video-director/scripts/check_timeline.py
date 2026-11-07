#!/usr/bin/env python3
"""Validate a timeline.json (schema in references/briefs.md) before any code is written.

Usage: python3 check_timeline.py timeline.json

ERRORs (exit 1) are things that break sync or the film: gaps between scenes, beats outside
the film, a loop that isn't whole bars, SFX pointing at beats that don't exist, no hook text
legible by 3 s (or a CTA that only appears later), a hook/CTA/term declared below its size
floor, and a listed term that is never said or shown.
WARNs are craft smells: a hero moment spent early, no silence before it, reads and texts held
too briefly to land, captions faster than 3.5 words/s (7 characters/s in Chinese, Japanese
and Korean; mixed text adds up both), a seam with no reason, overlapping scenes, VO timings still ESTIMATED, no terms
listed, a term said but not shown (or shown but not said).
A term matches as whole words, allowing a plural; in unspaced CJK text, as a substring.
Extra fields are allowed: the schema is a floor, not a cage. A field of the wrong shape is an
ERROR, not a crash.
"""
import json
import math
import re
import sys
from pathlib import Path

HOOK_BY = 3.0
TEXT_FLOORS = {"hook": 84, "cta": 48, "term": 48}  # font px at a 1080 short side (craft.md §6)
CAPTION_WPS, CAPTION_CJK_CPS = 3.5, 7.0  # craft.md §2


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def cjk_char(c):
    return ("\u3040" <= c <= "\u30ff" or "\u3400" <= c <= "\u9fff" or "\uac00" <= c <= "\ud7a3"
            or "\uf900" <= c <= "\ufaff" or "\uff66" <= c <= "\uff9f")


def count(text):
    """(CJK characters, Latin-style words): mixed text is read as the sum of both."""
    text = str(text)
    cjk = sum(cjk_char(c) for c in text)
    words = "".join(" " if cjk_char(c) else c for c in text).split()
    # beside CJK, a token that is only punctuation isn't a word; in Latin text the old count stands
    return cjk, sum(any(c.isalnum() for c in w) for w in words) if cjk else len(words)


def norm(s):
    return " ".join(re.sub(r"[^\w+#%]+", " ", str(s).lower()).split())  # keeps C++, C# and 50% whole


def joins(c):
    """Would this neighbour make a match part of a longer word? CJK runs on without spaces."""
    return (c.isalnum() or c in "_+#%") and not cjk_char(c)


def term_in(term, text):
    """Whole words, allowing a plural. Unspaced CJK text is matched as a substring."""
    term, text = norm(term), norm(text)
    if not term:
        return False
    if any(cjk_char(c) for c in term) or not any(c.isalnum() for c in term):
        return term.replace(" ", "") in text.replace(" ", "")
    stem = re.escape(term[:-1]) + "(?:y|ies|ys)" if term.endswith("y") else re.escape(term) + "(?:s|es)?"
    for m in re.finditer(stem, text):
        before, after = text[m.start() - 1:m.start()], text[m.end():m.end() + 1]
        if not (before and joins(before)) and not (after and joins(after)):
            return True
    return False


def read_time(text):  # craft.md §2
    cjk, words = count(text)
    return max(1.5, cjk / 4.5 + 1.5 + 0.3 * words) if cjk else max(1.5, 1.0 + 0.3 * words)


def caption_rate(text, secs):
    """(rate, limit, unit) for a caption on screen for secs. A word counts as two CJK characters."""
    cjk, words = count(text)
    if cjk:
        return (cjk + words * CAPTION_CJK_CPS / CAPTION_WPS) / secs, CAPTION_CJK_CPS, "characters/s"
    return words / secs, CAPTION_WPS, "words/s"


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except OSError as e:
        report([f"can't read {path}: {e.strerror}"], [])
    except ValueError as e:  # bad JSON, or not UTF-8
        report([f"{path} is not valid JSON: {e}"], [])


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    tl = read_json(sys.argv[1])
    errors, warns = [], []
    err, warn = errors.append, warns.append
    if not isinstance(tl, dict):
        err("the timeline must be a JSON object (schema in references/briefs.md)")
        report(errors, warns)

    def dicts(value, label):
        """The dict entries of a list field; anything else in it is an error."""
        if value is None:
            return []
        if not isinstance(value, list):
            err(f"{label} must be a list")
            return []
        for x in value:
            if not isinstance(x, dict):
                err(f"{label}: entry {x!r} must be an object")
        return [x for x in value if isinstance(x, dict)]

    def numbers(value, label):
        if value is not None and not isinstance(value, list):
            err(f"{label} must be a list")
            return []
        return value or []

    meta = tl.get("meta") if isinstance(tl.get("meta"), dict) else {}
    for k in ("w", "h", "fps", "dur"):
        if not (is_num(meta.get(k)) and meta[k] > 0):
            err(f"meta.{k} must be a positive number")
    if errors:
        report(errors, warns)
    dur, fps = float(meta["dur"]), float(meta["fps"])
    frame = 1.0 / fps
    clock = meta.get("clock")
    if clock not in ("music", "voice", "reads"):
        err('meta.clock must be "music", "voice" or "reads"')

    if clock == "music":
        meter = re.fullmatch(r"([1-9]\d*)/[1-9]\d*", str(meta.get("meter", "4/4")))
        if not (is_num(meta.get("bpm")) and meta["bpm"] > 0):
            err("music clock needs a positive meta.bpm")
        elif not meter:
            err(f"meta.meter {meta.get('meter')!r} should look like 4/4")
        elif meta.get("loop"):
            bar = int(meter.group(1)) * 60.0 / float(meta["bpm"])
            n = dur / bar
            if abs(n - round(n)) * bar > 0.002:
                err(f"loop is {n:.3f} bars; a music loop must be whole bars ({bar:.4f} s each)")

    scenes = dicts(tl.get("scenes"), "scenes")
    if not scenes:
        err("no scenes")
    beat_names, beat_t = set(), {}
    prev_end = 0.0
    for i, s in enumerate(scenes):
        sid, a, b = s.get("id", f"#{i}"), s.get("start"), s.get("end")
        if not (is_num(a) and is_num(b) and a < b):
            err(f"scene {sid}: needs numeric start < end")
            continue
        if a - prev_end > frame:
            err(f"scene {sid}: gap {prev_end:.3f}-{a:.3f} s (empty frames read as loading)")
        elif prev_end - a > frame:
            warn(f"scene {sid}: overlaps the scene before it by {prev_end - a:.3f} s")
        prev_end = max(prev_end, b)
        beats = s.get("beats", {})
        if not isinstance(beats or [], (dict, list)):
            err(f"scene {sid}: beats must be an object or a list")
            beats = []
        items = beats.items() if isinstance(beats, dict) else enumerate(beats or [])
        for name, t in items:
            beat_names.add(f"{sid}.{name}")
            if is_num(t):
                beat_t[f"{sid}.{name}"] = float(t)
            if not is_num(t):
                err(f"beat {sid}.{name} is not a number (keep refs like cueRef in a separate field)")
            elif not 0 <= t <= dur:
                err(f"beat {sid}.{name} = {t} is outside the film")
            elif not a - frame <= t <= b + frame:
                warn(f"beat {sid}.{name} = {t} lies outside its scene {a}-{b}")
        if i < len(scenes) - 1:
            tr = s.get("transitionOut")
            if not (isinstance(tr, dict) and tr.get("why")):
                warn(f"scene {sid}: transitionOut has no 'why' (every seam needs a reason you can say)")
    if scenes and abs(prev_end - dur) > frame:
        err(f"scenes end at {prev_end:.3f} s but meta.dur is {dur:.3f} s")

    reads = dicts(tl.get("reads"), "reads")
    for s in scenes:
        reads += dicts(s.get("reads"), f"scene {s.get('id')}: reads")
    for r in reads:
        f, t = r.get("from"), r.get("to")
        if is_num(f) and is_num(t):
            if t - f < 0.6:
                warn(f"read '{r.get('what', '?')}' gets {t - f:.2f} s: too short to find, understand, register")

    for t in numbers(tl.get("cuts"), "cuts"):
        if not (is_num(t) and 0 < t < dur):
            err(f"cut {t} is outside the film")

    hero_field = tl.get("hero")
    if hero_field is not None and not isinstance(hero_field, dict):
        err('hero must be an object: { "t": seconds, "what": "..." }')
        hero_field = {}
    hero_raw = (hero_field or {}).get("t")
    sil = [x for x in dicts(tl.get("silences"), "silences") if is_num(x.get("from")) and is_num(x.get("to"))]
    for x in sil:
        if x["to"] <= x["from"]:
            err(f"silence {x['from']}-{x['to']} ends before it starts")
        elif x["from"] < 0 or x["to"] > dur + frame:
            err(f"silence {x['from']}-{x['to']} is outside the film")
        elif x["to"] - x["from"] < 0.4:
            warn(f"silence {x['from']}-{x['to']} is under 0.4 s: it won't register")
    if not is_num(hero_raw):
        warn("no hero.t: name the one moment the film builds to")
    else:
        hero = float(hero_raw)
        if not 0 <= hero <= dur:
            err(f"hero.t = {hero} is outside the film")
        elif hero < 0.4 * dur:
            warn(f"hero moment at {hero:.2f} s ({hero / dur:.0%}): spent early?")
        if not any(x["to"] <= hero + 0.05 and hero - x["to"] <= 4.0 for x in sil):
            warn("no planned silence in the 4 s before the hero moment")

    for c in dicts(tl.get("sfx"), "sfx"):
        at = c.get("at")
        if isinstance(at, str) and "." in at and at not in beat_names and not at.split(".")[0] == "t":
            err(f"sfx at '{at}' refers to a beat that doesn't exist")

    captions = dicts(tl.get("captions"), "captions")
    for c in captions:
        f, t, text = c.get("from"), c.get("to"), str(c.get("text", ""))
        if is_num(f) and is_num(t) and t > f:
            if t - f < 0.7:
                warn(f"caption '{text[:30]}' is on screen {t - f:.2f} s (< 0.7 s)")
            rate, limit, unit = caption_rate(text, t - f)
            if rate > limit:
                warn(f"caption '{text[:30]}' runs {rate:.1f} {unit} (> {limit:g})")

    # texts: from/to in seconds, or in/out naming beats ("scene.beat")
    texts = []
    for x in dicts(tl.get("texts"), "texts"):
        for key in ("in", "out"):
            if x.get(key) is not None and str(x[key]) not in beat_t:
                err(f"text '{str(x.get('text', x.get('id', '?')))[:30]}': {key} '{x[key]}' is not a beat")
        f = x.get("from") if is_num(x.get("from")) else beat_t.get(str(x.get("in")))
        t = x.get("to") if is_num(x.get("to")) else beat_t.get(str(x.get("out")))
        texts.append({**x, "from": f, "to": t})
        label = str(x.get("text", x.get("id", "?")))[:30]
        if f is not None and f >= dur:
            err(f"text '{label}' appears at {f:g} s, after the film ends")
        if f is not None and t is not None and t - f < read_time(x.get("text", "")) - frame:
            warn(f"text '{label}' holds {t - f:.2f} s; it needs {read_time(x.get('text', '')):.2f} s to be read")
        role, px = x.get("role"), x.get("px")
        if isinstance(role, str) and role in TEXT_FLOORS:
            if not is_num(px):
                warn(f"{role} '{label}' has no px: declare its rendered font size so the floor can be checked")
            elif px * 1080 / min(meta["w"], meta["h"]) < TEXT_FLOORS[role]:
                err(f"{role} '{label}' is {px} px: below the {TEXT_FLOORS[role]} px floor (at a 1080 short side)")

    # hook: sound off, the first 3 s say what this is (SKILL.md principle 1)
    def first(role):
        ts = [x["from"] for x in texts if x.get("role") == role and x["from"] is not None]
        return min(ts) if ts else None
    hook, cta, waiver = first("hook"), first("cta"), meta.get("hookWaiver")
    if hook is None or hook > HOOK_BY:
        msg = (f"hook text first legible at {hook:.2f} s" if hook is not None else "no texts[] entry with role 'hook'")
        msg += f": by {HOOK_BY:g} s, sound off, large type must say what this is"
        (warn if waiver else err)(msg + (f" (waived: {waiver})" if waiver else ""))
    if cta is not None and cta > HOOK_BY:
        (warn if waiver else err)(f"CTA first appears at {cta:.2f} s: show it by {HOOK_BY:g} s too "
                                  "(it can return at the end)")

    # terms: the words this audience searches for are said and shown (SKILL.md principle 13)
    vo = dicts(tl.get("vo"), "vo")
    for l in vo:
        l["words"] = dicts(l.get("words"), f"VO line {l.get('id', '?')}: words")
    said = " ".join(str(l.get("text") or " ".join(str(w.get("w", "")) for w in l["words"])) for l in vo)
    shown = " ".join(str(c.get("text", "")) for c in captions + texts)
    terms = numbers(tl.get("terms"), "terms")
    if not terms:
        warn("no terms: list the 1-3 words this audience would search for (the subject's name, key properties)")
    for term in terms:
        in_vo, on_screen = term_in(term, said), term_in(term, shown)
        if not in_vo and not on_screen:
            err(f"term '{term}' is never said or shown: name it right after the intuition it labels")
        elif vo and not in_vo:
            warn(f"term '{term}' is shown but never said")
        elif not on_screen:
            warn(f"term '{term}' is said but never on screen: muted viewers miss it")

    vo_meta = meta.get("vo") if isinstance(meta.get("vo"), dict) else {}
    status = str(vo_meta.get("status", "")) + " " + " ".join(str(l.get("status", "")) for l in vo)
    if vo and "ESTIMATED" in status.upper():
        warn("VO timings are ESTIMATED: replace with real word timestamps before stills (phase 3)")
    for line in vo:
        ts = [w.get("t") for w in line["words"] if is_num(w.get("t"))]
        if ts != sorted(ts):
            err(f"VO line {line.get('id', '?')}: word times are not increasing")

    report(errors, warns)


def report(errors, warns):
    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN ", w)
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
