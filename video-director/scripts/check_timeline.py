#!/usr/bin/env python3
"""Validate a timeline.json (schema in references/briefs.md) before any code is written.

Usage: python3 check_timeline.py timeline.json

ERRORs (exit 1) are things that break sync or the film: gaps between scenes, beats outside
the film, a loop that isn't whole bars, SFX pointing at beats that don't exist.
WARNs are craft smells: a hero moment spent early, no silence before it, reads too short to
land, captions faster than 3.5 words/s, a seam with no reason, VO timings still ESTIMATED.
Extra fields are allowed: the schema is a floor, not a cage.
"""
import json
import sys
from pathlib import Path


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    tl = json.loads(Path(sys.argv[1]).read_text())
    errors, warns = [], []
    err, warn = errors.append, warns.append

    meta = tl.get("meta", {})
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
        if not is_num(meta.get("bpm")):
            err("music clock needs meta.bpm")
        elif meta.get("loop"):
            beats_per_bar = int(str(meta.get("meter", "4/4")).split("/")[0])
            bar = beats_per_bar * 60.0 / float(meta["bpm"])
            n = dur / bar
            if abs(n - round(n)) * bar > 0.002:
                err(f"loop is {n:.3f} bars; a music loop must be whole bars ({bar:.4f} s each)")

    scenes = tl.get("scenes", [])
    if not scenes:
        err("no scenes")
    beat_names = set()
    prev_end = 0.0
    for i, s in enumerate(scenes):
        sid, a, b = s.get("id", f"#{i}"), s.get("start"), s.get("end")
        if not (is_num(a) and is_num(b) and a < b):
            err(f"scene {sid}: needs numeric start < end")
            continue
        if a - prev_end > frame:
            err(f"scene {sid}: gap {prev_end:.3f}-{a:.3f} s (empty frames read as loading)")
        prev_end = max(prev_end, b)
        beats = s.get("beats", {})
        items = beats.items() if isinstance(beats, dict) else enumerate(beats or [])
        for name, t in items:
            beat_names.add(f"{sid}.{name}")
            if not is_num(t):
                err(f"beat {sid}.{name} is not a number (keep refs like cueRef in a separate field)")
            elif not 0 <= t <= dur:
                err(f"beat {sid}.{name} = {t} is outside the film")
            elif not a - frame <= t <= b + frame:
                warn(f"beat {sid}.{name} = {t} lies outside its scene {a}-{b}")
        if i < len(scenes) - 1:
            tr = s.get("transitionOut") or {}
            if not tr.get("why"):
                warn(f"scene {sid}: transitionOut has no 'why' (every seam needs a reason you can say)")
    if scenes and abs(prev_end - dur) > frame:
        err(f"scenes end at {prev_end:.3f} s but meta.dur is {dur:.3f} s")

    reads = list(tl.get("reads", [])) + [r for s in scenes for r in s.get("reads", [])]
    for r in reads:
        f, t = r.get("from"), r.get("to")
        if is_num(f) and is_num(t):
            if t - f < 0.6:
                warn(f"read '{r.get('what', '?')}' gets {t - f:.2f} s: too short to find, understand, register")

    for t in tl.get("cuts", []):
        if not (is_num(t) and 0 < t < dur):
            err(f"cut {t} is outside the film")

    hero_raw = (tl.get("hero") or {}).get("t")
    if not is_num(hero_raw):
        warn("no hero.t: name the one moment the film builds to")
    else:
        hero = float(hero_raw)
        if not 0 <= hero <= dur:
            err(f"hero.t = {hero} is outside the film")
        elif hero < 0.4 * dur:
            warn(f"hero moment at {hero:.2f} s ({hero / dur:.0%}): spent early?")
        sil = [x for x in tl.get("silences", []) if is_num(x.get("from")) and is_num(x.get("to"))]
        if not any(x["to"] <= hero + 0.05 and hero - x["to"] <= 4.0 for x in sil):
            warn("no planned silence in the 4 s before the hero moment")
        for x in sil:
            if x["to"] - x["from"] < 0.4:
                warn(f"silence {x['from']}-{x['to']} is under 0.4 s: it won't register")

    for c in tl.get("sfx", []):
        at = c.get("at")
        if isinstance(at, str) and "." in at and at not in beat_names and not at.split(".")[0] == "t":
            err(f"sfx at '{at}' refers to a beat that doesn't exist")

    for c in tl.get("captions", []):
        f, t, text = c.get("from"), c.get("to"), str(c.get("text", ""))
        if is_num(f) and is_num(t) and t > f:
            words = len(text.split())
            if t - f < 0.7:
                warn(f"caption '{text[:30]}' is on screen {t - f:.2f} s (< 0.7 s)")
            if words / (t - f) > 3.5:
                warn(f"caption '{text[:30]}' runs {words / (t - f):.1f} words/s (> 3.5)")

    vo = tl.get("vo")
    vo_meta = meta.get("vo") if isinstance(meta.get("vo"), dict) else {}
    status = str(vo_meta.get("status", "")) + " " + " ".join(str(l.get("status", "")) for l in vo or [])
    if vo and "ESTIMATED" in status.upper():
        warn("VO timings are ESTIMATED: replace with real word timestamps before stills (phase 3)")
    for line in vo or []:
        ts = [w.get("t") for w in line.get("words", []) if is_num(w.get("t"))]
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
