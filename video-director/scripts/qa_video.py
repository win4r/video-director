#!/usr/bin/env python3
"""Post-render QA for a coded video: measure what you can't watch or hear.

Usage:
  python3 qa_video.py film.mp4 --out qa/ [--beats timeline.json | --times 1.0,2.5,...]
                      [--offset 0.3] [--loop] [--freeze 1.0] [--expect-cuts 4.0,8.0]

Produces in --out:
  report.md / report.json   PASS / WARN / FAIL per check, with timestamps
  beats_sheet.jpg           one frame per beat, taken `offset` s after it (or evenly spaced)
  phone_sheet.jpg           1 fps at 360 px wide: can a phone viewer read it?
  hook_sheet.jpg            0-3 s every 0.5 s at 360 px wide: the muted-autoplay test

Checks: hook, CTA and term texts (timeline texts[] with a role and a box: rendered font size
and contrast against their floors), frame 0 (black/flat), single-frame flashes, pops (small
spikes), detected cuts vs planned cuts, frozen stretches, flat frames, loop seam (position + speed), integrated
loudness and true peak (ebur128), loudest 100 ms, silences and whether one precedes the peak,
and whether the timeline's planned silences are actually quiet.

A "silence" here (and in references/sound.md) is >= 0.4 s whose 100 ms RMS stays at least
--silence-rel dB (default 15) below the film's 90th-percentile level AND below --silence-abs
dBFS (default -30), so a quiet bed under a loud film doesn't count as silence. With --beats, the
timeline's meta.loop turns on the loop check and meta.clock == "voice" makes the
loudest-moment check advisory (the voice is usually the loudest thing in a narrated film).

Needs ffmpeg/ffprobe on PATH, numpy and Pillow. Exit code 1 if any check FAILs.
"""
import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ANALYSIS_W = 192  # analysis frames are tiny greyscale copies; plenty for diffs and contrast


def run_bytes(cmd) -> bytes:
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr.decode(errors='replace')[-800:]}")
    return r.stdout


def run(cmd) -> str:
    return run_bytes(cmd).decode()


def probe(path):
    out = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,r_frame_rate:format=duration",
                          "-of", "json", str(path)]))
    v = next((s for s in out["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        raise RuntimeError("no video stream")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    return {"w": int(v["width"]), "h": int(v["height"]), "fps": num / den,
            "dur": float(out["format"]["duration"]),
            "audio": any(s["codec_type"] == "audio" for s in out["streams"])}


# ---------------------------------------------------------------- picture analysis

def frame_stats(path, info):
    """Stream tiny greyscale frames; keep per-frame stats, never the whole film."""
    aw = ANALYSIS_W
    ah = max(2, int(round(aw * info["h"] / info["w"] / 2)) * 2)
    size = aw * ah
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                             f"scale={aw}:{ah}:flags=area,format=gray", "-f", "rawvideo", "-"],
                            stdout=subprocess.PIPE)
    mean, std, d, skip = [], [], [], []
    prev = prev2 = first = None
    assert proc.stdout is not None
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        f = np.frombuffer(buf, np.uint8).reshape(ah, aw).astype(np.int16)
        mean.append(float(f.mean()))
        std.append(float(f.std()))
        d.append(float(np.abs(f - prev).mean()) if prev is not None else 0.0)
        # skip[n] = |f[n+1] - f[n-1]|, stored at index n (computed when f[n+1] arrives)
        if prev2 is not None:
            skip.append(float(np.abs(f - prev2).mean()))
        if first is None:
            first = f
        prev2, prev = prev, f
    proc.wait()
    n = len(mean)
    skip = [math.nan] + skip + [math.nan] if n >= 2 else [math.nan] * n
    seam = float(np.abs(prev - first).mean()) if (n >= 2 and prev is not None and first is not None) else math.nan
    return {"n": n, "mean": np.array(mean), "std": np.array(std), "d": np.array(d),
            "skip": np.array(skip[:n]), "seam": seam}


def runs(mask):
    """[start, end) index pairs of consecutive True values."""
    out, start = [], None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def analyse_picture(st, fps, args):
    d, skip, n = st["d"], st["skip"], st["n"]
    res = {}
    med = float(np.median(d[1:])) if n > 2 else 0.0

    # single-frame flashes: frame n differs from both neighbours, but n-1 ~ n+1
    t_flash = max(2.0, 4 * med)
    flashes = [i for i in range(1, n - 1)
               if d[i] > t_flash and d[i + 1] > t_flash
               and skip[i] < 0.35 * min(d[i], d[i + 1])]
    flash_frames = set(flashes) | {i + 1 for i in flashes}

    # cuts: a persistent jump well above the local motion level
    cuts = []
    for i in range(1, n):
        if i in flash_frames:
            continue
        lo, hi = max(1, i - 15), min(n, i + 16)
        local = np.concatenate([d[lo:i], d[i + 1:hi]])
        lm = float(np.median(local)) if local.size else 0.0
        if d[i] > max(6.0, 3.5 * (lm + 0.5)):
            cuts.append(i)
    # pops: smaller spikes (3x both neighbours) that are neither cuts nor flashes
    pops = [i for i in range(1, n - 1)
            if i not in flash_frames and i not in cuts
            and d[i] > 2.0 and d[i] > 3 * max(d[i - 1], d[i + 1])]

    # frozen stretches and flat (near-uniform) frames
    still = d < args.freeze_eps
    if n:
        still[0] = False  # d[0] has no previous frame
    frozen = [(a, b) for a, b in runs(still) if (b - a + 1) / fps >= args.freeze]
    flat = [(a, b) for a, b in runs(st["std"] < 6.0) if a > 0]

    res["frame0"] = {"mean": round(st["mean"][0], 1), "contrast": round(st["std"][0], 1)}
    res["flashes"] = [round(i / fps, 3) for i in flashes]
    res["pops"] = [round(i / fps, 3) for i in pops]
    res["cuts"] = [round(i / fps, 3) for i in cuts]
    res["frozen"] = [{"from": round((a - 1) / fps, 2), "to": round(b / fps, 2),
                      "secs": round((b - a + 1) / fps, 2), "to_end": b >= n} for a, b in frozen]
    res["flat"] = [{"from": round(a / fps, 2), "to": round(b / fps, 2)} for a, b in flat]
    res["median_step"] = round(med, 3)

    if args.loop and n > 3:
        v_in, v_out = d[n - 1], d[1]
        res["loop"] = {"seam": round(st["seam"], 3),
                       "seam_vs_median": round(st["seam"] / (med + 1e-6), 2),
                       "speed_ratio": round((v_in + 0.05) / (v_out + 0.05), 2)}
    return res


def compare_cuts(detected, expected, fps):
    if not expected:
        return None
    errs, missing = [], []
    for t in expected:
        if not detected:
            missing.append(t)
            continue
        near = min(detected, key=lambda c: abs(c - t))
        if abs(near - t) > 0.5:
            missing.append(t)
        else:
            errs.append(round((near - t) * fps, 2))
    unplanned = [c for c in detected if all(abs(c - t) > 0.5 for t in expected)]
    return {"max_err_frames": max((abs(e) for e in errs), default=0.0), "errors_frames": errs,
            "missing": missing, "unplanned": unplanned}


# ---------------------------------------------------------------- audio analysis

def analyse_audio(path, args, planned=None):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-map", "0:a:0",
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = r.stderr.decode(errors="replace")
    summary = log[log.rfind("Summary:"):] if "Summary:" in log else ""
    i_m = re.search(r"I:\s+(-?[\d.]+|-inf)\s+LUFS", summary)
    p_m = re.search(r"True peak:\s+Peak:\s+(-?[\d.]+|-inf)\s+dBFS", summary)
    res: dict = {"lufs": float(i_m.group(1)) if i_m else None,
           "true_peak": float(p_m.group(1)) if p_m else None}

    sr = 16000
    raw = run_bytes(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "1",
                     "-ar", str(sr), "-f", "f32le", "-"])
    x = np.frombuffer(raw, np.float32)
    win, hop = int(0.1 * sr), int(0.05 * sr)
    if x.size < win:
        return res
    nwin = 1 + (x.size - win) // hop
    rms = np.array([math.sqrt(float(np.mean(x[k * hop:k * hop + win] ** 2)) + 1e-12)
                    for k in range(nwin)])
    db = 20 * np.log10(rms)
    k = int(np.argmax(db))
    res["loudest_at"] = round((k * hop + win / 2) / sr, 2)
    res["loudest_db"] = round(float(db[k]), 1)
    p90 = float(np.percentile(db, 90))
    thresh = min(p90 - args.silence_rel, args.silence_abs)
    res["p90_db"] = round(p90, 1)
    res["silence_threshold_db"] = round(thresh, 1)
    quiet = runs(db < thresh)
    sil = [((a * hop) / sr, ((b - 1) * hop + win) / sr) for a, b in quiet]
    sil = [(s0, s1) for s0, s1 in sil if s1 - s0 >= 0.4]
    res["silences"] = [{"from": round(a, 2), "to": round(b, 2)} for a, b in sil]
    t_peak = res["loudest_at"]
    res["silence_before_peak"] = any(s1 <= t_peak + 0.05 and t_peak - s1 <= 4.0 for _, s1 in sil)
    res["planned_silences"] = []
    for ps in planned or []:
        a, b = float(ps["from"]), float(ps["to"])
        inside = [db[j] for j in range(nwin) if j * hop / sr >= a and (j * hop + win) / sr <= b]
        if not inside:
            continue
        loudest_inside = float(max(inside))
        res["planned_silences"].append({"from": a, "to": b, "max_db": round(loudest_inside, 1),
                                        "depth_db": round(p90 - loudest_inside, 1),
                                        "ok": loudest_inside < thresh})
    return res


# ---------------------------------------------------------------- contact sheets

def grab(path, t, width, tmp, name):
    out = Path(tmp) / f"{name}.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(t, 0):.3f}", "-i", str(path),
         "-frames:v", "1", "-vf", f"scale={width}:-2", str(out)])
    return Image.open(out).convert("RGB") if out.exists() else None


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def sheet(path, times, width, cols, fps, dest, tmp):
    tiles = []
    for i, t in enumerate(times):
        im = grab(path, t, width, tmp, f"{Path(dest).stem}_{i:04d}")
        if im is None:
            continue
        lab = ImageDraw.Draw(im)
        txt = f"{t:.2f}s  f{int(round(t * fps))}"
        f = font(max(12, width // 22))
        lab.rectangle([0, 0, im.width, int(getattr(f, "size", 12)) + 8], fill=(0, 0, 0))
        lab.text((6, 4), txt, fill=(255, 255, 255), font=f)
        tiles.append(im)
    if not tiles:
        return None
    tw, th = tiles[0].size
    rows = math.ceil(len(tiles) / cols)
    canvas = Image.new("RGB", (cols * tw + (cols - 1) * 4, rows * th + (rows - 1) * 4), (40, 40, 40))
    for i, im in enumerate(tiles):
        canvas.paste(im, ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
    canvas.save(dest, quality=88)
    return str(dest)


def measure_text(im, box, short):
    """Cap height (px at a 1080 short side) and contrast of the text inside box = [x, y, w, h].

    The box is the text's own bounds, not its container. Otsu splits the crop's luminance in
    two and the smaller class is taken as the glyphs. Height runs from the top of the tallest
    glyphs to the baseline (the last row still dense with ink), so descenders don't count:
    caps and ascenders sit at about 0.72 of the font size in most faces, so font_px = cap / 0.72
    (within ~2 px of the set size on Inter and JetBrains Mono).
    """
    x, y, w, h = (int(round(float(v))) for v in box)
    rgb = np.asarray(im.crop((x, y, x + w, y + h)), np.float64) / 255
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    hist, edges = np.histogram(lum, 256, (0, 1))
    p = hist / max(1, hist.sum())
    w0 = np.cumsum(p)
    mu = np.cumsum(p * edges[:-1])
    between = (mu[-1] * w0 - mu) ** 2 / (w0 * (1 - w0) + 1e-12)
    hi = lum > edges[int(np.argmax(between))]
    ink = hi if hi.mean() <= 0.5 else ~hi
    if ink.all() or not ink.any():
        return {"font_px": 0.0, "contrast": 1.0}
    l_ink, l_bg = float(np.median(lum[ink])), float(np.median(lum[~ink]))
    contrast = (max(l_ink, l_bg) + 0.05) / (min(l_ink, l_bg) + 0.05)
    rows = ink.sum(axis=1)
    dense = np.nonzero(rows >= 0.25 * rows.max())[0]
    top = np.nonzero(rows >= max(1, 0.03 * rows.max()))[0][0]
    cap = float(dense[-1] - top + 1) * 1080 / short
    return {"font_px": round(cap / 0.72, 1), "contrast": round(contrast, 1)}


TEXT_FLOORS = {"hook": 84, "cta": 48, "term": 48}  # font px at a 1080 short side (craft.md §6)
MIN_CONTRAST = 7.0


def beat_times(tl):
    """'scene.beat' -> seconds, for fields that point at beats by name."""
    out = {}
    for s in tl.get("scenes", []):
        b = s.get("beats")
        for k, v in (b.items() if isinstance(b, dict) else []):
            if isinstance(v, (int, float)):
                out[f"{s.get('id')}.{k}"] = float(v)
    return out


def load_timeline(path):
    tl = json.loads(Path(path).read_text())
    nums = lambda xs: [float(v) for v in xs if isinstance(v, (int, float))]
    beats, cuts, hero = [], [], None
    if isinstance(tl, list):
        return {"beats": sorted(set(nums(tl))), "cuts": [], "hero": None,
                "silences": [], "loop": False, "clock": None, "texts": []}
    for s in tl.get("scenes", []):
        if isinstance(s.get("start"), (int, float)):
            beats.append(float(s["start"]))
        b = s.get("beats")
        beats += nums(b.values()) if isinstance(b, dict) else nums(b or [])
    beats += nums(tl.get("beats", []) if isinstance(tl.get("beats"), list) else [])
    cuts = nums(tl.get("cuts", []))
    if isinstance(tl.get("hero"), dict):
        hero = tl["hero"].get("t")
    meta = tl.get("meta", {}) if isinstance(tl.get("meta"), dict) else {}
    sil = [x for x in tl.get("silences", []) if isinstance(x, dict) and "from" in x and "to" in x]
    named = beat_times(tl)
    texts = []
    for x in tl.get("texts", []):
        if isinstance(x, dict) and x.get("role") in TEXT_FLOORS:
            t = x.get("from") if isinstance(x.get("from"), (int, float)) else named.get(x.get("in"))
            texts.append({"text": str(x.get("text", x.get("id", "?"))), "role": x["role"],
                          "from": t, "box": x.get("box")})
    return {"beats": sorted(set(beats)), "cuts": cuts, "hero": hero, "silences": sil,
            "loop": bool(meta.get("loop")), "clock": meta.get("clock"), "texts": texts}


# ---------------------------------------------------------------- report

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", default="qa")
    ap.add_argument("--beats", help="timeline.json (scenes[].start/beats, cuts, hero.t)")
    ap.add_argument("--times", help="comma-separated beat times in seconds")
    ap.add_argument("--offset", type=float, default=0.3, help="seconds after each beat to sample")
    ap.add_argument("--expect-cuts", help="comma-separated planned cut times (overrides timeline cuts)")
    ap.add_argument("--loop", action="store_true", help="check the loop seam")
    ap.add_argument("--freeze", type=float, default=1.0, help="report frozen stretches at least this long (s)")
    ap.add_argument("--freeze-eps", type=float, default=0.25, help="mean abs diff (0-255) counted as frozen")
    ap.add_argument("--silence-rel", type=float, default=15.0,
                    help="silence = 100 ms RMS at least this many dB below the film's p90 level")
    ap.add_argument("--silence-abs", type=float, default=-30.0,
                    help="...and below this absolute level (dBFS)")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.0, help="max true peak, dBTP")
    args = ap.parse_args()

    video = Path(args.video)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    info = probe(video)
    fps, dur = info["fps"], info["dur"]

    beats: list = []
    planned_cuts: list = []
    planned_sil: list = []
    texts: list = []
    hero = clock = None
    if args.beats:
        tl = load_timeline(args.beats)
        beats, planned_cuts, hero = tl["beats"], tl["cuts"], tl["hero"]
        planned_sil, clock, texts = tl["silences"], tl["clock"], tl["texts"]
        args.loop = args.loop or tl["loop"]
    if args.times:
        beats = sorted(float(x) for x in args.times.split(",") if x.strip())
    if args.expect_cuts:
        planned_cuts = sorted(float(x) for x in args.expect_cuts.split(",") if x.strip())

    st = frame_stats(video, info)
    pic = analyse_picture(st, fps, args)
    cutcmp = compare_cuts(pic["cuts"], planned_cuts, fps)
    aud = analyse_audio(video, args, planned_sil) if info["audio"] else None

    with tempfile.TemporaryDirectory() as tmp:
        sample = [min(b + args.offset, dur - 1 / fps) for b in beats] if beats else \
                 [i * max(0.5, dur / 24) for i in range(int(dur / max(0.5, dur / 24)) + 1)]
        sample = [t for t in sample if t < dur][:60]
        beat_sheet = sheet(video, sample, 480, 4, fps, out / "beats_sheet.jpg", tmp)
        phone_t = [float(t) + 0.5 for t in range(int(dur))][:60] or [0.0]
        phone_sheet = sheet(video, phone_t, 360, 6, fps, out / "phone_sheet.jpg", tmp)
        hook_t = [i * 0.5 for i in range(7) if i * 0.5 < dur]
        hook_sheet = sheet(video, hook_t, 360, 7, fps, out / "hook_sheet.jpg", tmp)
        for i, x in enumerate(texts):
            if isinstance(x["from"], (int, float)) and isinstance(x["box"], list) and len(x["box"]) == 4:
                t = min(float(x["from"]) + 0.1, dur - 1 / fps)
                im = grab(video, t, info["w"], tmp, f"text_{i:02d}")
                x.update(measure_text(im, x["box"], min(info["w"], info["h"])) if im else {}, at=round(t, 2))

    checks = []

    def add(level, name, msg):
        checks.append({"level": level, "check": name, "detail": msg})

    f0 = pic["frame0"]
    if f0["contrast"] < 6 or f0["mean"] < 8:
        add("FAIL", "frame 0", f"flat or black (mean {f0['mean']}, contrast {f0['contrast']}): thumbnails and muted autoplay show this")
    else:
        add("PASS", "frame 0", f"mean {f0['mean']}, contrast {f0['contrast']}; still confirm it's a finished composition")
    if args.beats and not any(x["role"] == "hook" for x in texts):
        add("WARN", "hook text", "the timeline marks no texts[] role 'hook': judge hook_sheet.jpg by eye "
            "(sound off, first 3 s: can you say what it is and what to do?)")
    for x in texts:
        name, floor = f"{x['role']} text", TEXT_FLOORS[x["role"]]
        if "font_px" not in x:
            why = ("no time (from, or in naming a beat)" if not isinstance(x["from"], (int, float)) else
                   "no box [x, y, w, h]" if not (isinstance(x["box"], list) and len(x["box"]) == 4) else
                   "the frame could not be grabbed")
            add("WARN", name, f"'{x['text'][:40]}': {why}, so size and contrast are unmeasured; "
                "check hook_sheet.jpg")
            continue
        ok = x["font_px"] >= floor and x["contrast"] >= MIN_CONTRAST
        add("PASS" if ok else "FAIL", name,
            f"'{x['text'][:40]}' at {x['at']} s: ~{x['font_px']} px font (>= {floor}), "
            f"contrast {x['contrast']}:1 (>= {MIN_CONTRAST:g}:1)")
    add("FAIL" if pic["flashes"] else "PASS", "single-frame flashes",
        f"at {pic['flashes']}" if pic["flashes"] else "none")
    add("WARN" if pic["pops"] else "PASS", "pops",
        f"small spikes at {pic['pops']}: intended hits, or glitches/stray transitions?" if pic["pops"] else "none")
    if cutcmp:
        lvl = "PASS" if cutcmp["max_err_frames"] <= 1 and not cutcmp["missing"] else "FAIL"
        add(lvl, "cuts vs plan", f"max error {cutcmp['max_err_frames']} f; missing {cutcmp['missing']}; "
            f"unplanned {cutcmp['unplanned']}")
    else:
        add("INFO", "detected cuts", f"{pic['cuts']}")
    for fr in pic["frozen"]:
        tag = "final hold" if fr["to_end"] else "designed hold or dead air?"
        add("WARN", "frozen stretch", f"{fr['from']}-{fr['to']} s ({fr['secs']} s): {tag}")
    if pic["flat"]:
        add("WARN", "flat frames", f"near-uniform frames at {pic['flat'][:10]}: blank transition frames?")
    if "loop" in pic:
        lp = pic["loop"]
        # A mostly-still film has a median step near zero, so the ratio alone fails invisible seams;
        # under 0.5/255 mean difference nobody can see the join.
        ok = (lp["seam_vs_median"] <= 2.0 or lp["seam"] < 0.5) and 0.5 <= lp["speed_ratio"] <= 2.0
        add("PASS" if ok else "FAIL", "loop seam",
            f"seam {lp['seam']}/255 = {lp['seam_vs_median']}x median step (<=2, or <0.5/255), "
            f"speed in/out ratio {lp['speed_ratio']} (0.5-2)")
    if aud is None:
        add("INFO", "audio", "no audio stream")
    else:
        if aud["lufs"] is not None:
            ok = abs(aud["lufs"] - args.lufs) <= 1.0 and (aud["true_peak"] or -99) <= args.tp
            add("PASS" if ok else "FAIL", "loudness",
                f"{aud['lufs']} LUFS (target {args.lufs} +/-1), true peak {aud['true_peak']} dBTP (<= {args.tp})")
        if "loudest_at" in aud:
            msg = f"loudest 100 ms at {aud['loudest_at']} s ({aud['loudest_db']} dBFS)"
            if clock == "voice":
                add("INFO", "loudest moment", msg + "; voice clock: confirm the payoff hit is the loudest "
                    "non-voice sound and sits in a VO pause")
            elif hero is not None:
                gap = aud["loudest_at"] - float(hero)
                msg += f"; hero moment at {hero} s (offset {gap:+.2f} s)"
                add("PASS" if abs(gap) <= 0.5 else "WARN", "loudest moment", msg)
            else:
                add("INFO", "loudest moment", msg + "; is this the payoff?")
            add("PASS" if aud["silence_before_peak"] else "WARN", "silence before peak",
                f"silences >= 0.4 s below {aud['silence_threshold_db']} dBFS: "
                f"{aud['silences'][:8]}")
            for ps in aud.get("planned_silences", []):
                add("PASS" if ps["ok"] else "FAIL", "planned silence",
                    f"{ps['from']}-{ps['to']} s peaks at {ps['max_db']} dBFS, {ps['depth_db']} dB under p90 "
                    f"(needs < {aud['silence_threshold_db']} dBFS)")

    report = {"file": str(video), "info": info, "picture": pic, "cuts_vs_plan": cutcmp,
              "audio": aud, "texts": texts,
              "sheets": {"beats": beat_sheet, "phone": phone_sheet, "hook": hook_sheet}, "checks": checks}
    (out / "report.json").write_text(json.dumps(report, indent=2, default=float))
    lines = [f"# QA: {video.name}", "",
             f"{info['w']}x{info['h']} @ {fps:.3f} fps, {dur:.2f} s, audio: {info['audio']}", "",
             "| level | check | detail |", "|---|---|---|"]
    lines += [f"| {c['level']} | {c['check']} | {c['detail']} |" for c in checks]
    lines += ["", f"Sheets: {beat_sheet}, {phone_sheet}, {hook_sheet}",
              "Look at all three: numbers catch broken, not bad. The hook sheet is the muted test."]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if any(c["level"] == "FAIL" for c in checks) else 0)


if __name__ == "__main__":
    main()
