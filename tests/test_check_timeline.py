import copy
import json
import subprocess
import sys

import pytest

from conftest import SCRIPTS, load


def film(**extra):
    tl = {"meta": {"w": 1920, "h": 1080, "fps": 30, "dur": 10, "clock": "reads"},
          "scenes": [{"id": "a", "start": 0, "end": 5, "beats": {"x": 1, "y": 3},
                      "transitionOut": {"why": "the line carries on"}},
                     {"id": "b", "start": 5, "end": 10, "beats": {"z": 7}}],
          "hero": {"t": 7}, "silences": [{"from": 6, "to": 6.8}],
          "texts": [{"text": "Bloom filters", "from": 0.5, "to": 4, "role": "hook", "px": 100}],
          "terms": ["bloom filter"]}
    tl.update(extra)
    return tl


def check(tmp_path, tl):
    path = tmp_path / "t.json"
    path.write_text(tl if isinstance(tl, str) else json.dumps(tl, ensure_ascii=False))
    r = subprocess.run([sys.executable, str(SCRIPTS / "check_timeline.py"), str(path)],
                       capture_output=True, text=True)
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, r.stdout + r.stderr


def text(s):
    return [{"text": s, "from": 0.5, "to": 8, "role": "hook", "px": 100}]


def test_clean_film_passes(tmp_path):
    code, out = check(tmp_path, film())
    assert code == 0 and "0 error(s), 0 warning(s)" in out


# ---- terms

@pytest.mark.parametrize("term, shown", [
    ("bloom filter", "How a Bloom filter works"),
    ("bloom filter", "Bloom filters"),
    ("bloom filter", "BLOOM\nFILTER"),
    ("hash", "one hash, two hashes"),
    ("C++", "written in C++ today"),
    ("C#", "a C# library"),
    (".NET", "runs on .NET"),
    ("布隆过滤器", "这就是布隆过滤器的原理"),
    ("ブルームフィルタ", "ブルームフィルタとは何か"),
    ("布隆 过滤器", "这就是布隆过滤器的原理"),
    ("AI 代码", "这是 AI 代码工具"),
])
def test_term_found(tmp_path, term, shown):
    code, out = check(tmp_path, film(texts=text(shown), terms=[term]))
    assert code == 0, out


@pytest.mark.parametrize("term, shown", [
    ("C++", "cat pictures"),
    ("C++", "written in C today"),
    ("C#", "written in C today"),
    ("Go", "good things"),
    ("art", "start here"),
    ("布隆过滤器", "这就是过滤器的原理"),
    ("!!!", "anything at all"),
])
def test_term_not_found(tmp_path, term, shown):
    code, out = check(tmp_path, film(texts=text(shown), terms=[term]))
    assert code == 1 and "never said or shown" in out, out


def test_cjk_said_but_not_shown_warns(tmp_path):
    vo = [{"id": "L1", "text": "这就是布隆过滤器"}]
    code, out = check(tmp_path, film(vo=vo, terms=["布隆过滤器"], texts=text("原理")))
    assert code == 0 and "said but never on screen" in out


# ---- read time and caption rate

@pytest.mark.parametrize("s, hold, warns", [
    ("布隆过滤器的工作原理", 3.7, False),  # 10 chars / 4.5 + 1.5 = 3.72 s, less a frame
    ("布隆过滤器的工作原理", 3.0, True),
    ("短", 1.8, False),
    ("two words", 1.6, False),
    ("two words", 1.2, True),
])
def test_read_time(tmp_path, s, hold, warns):
    t = film(texts=text("Bloom filter") + [{"text": s, "from": 1, "to": 1 + hold}])
    code, out = check(tmp_path, t)
    assert code == 0 and ("to be read" in out) is warns, out


@pytest.mark.parametrize("s, secs, warns", [
    ("这是一段非常非常非常长的中文字幕内容需要很久才能读完", 1.0, True),
    ("这是一段字幕", 2.0, False),
    ("a caption of a few words", 2.0, False),
    ("a caption of a fair few more words than that", 1.0, True),
])
def test_caption_rate(tmp_path, s, secs, warns):
    code, out = check(tmp_path, film(captions=[{"from": 1, "to": 1 + secs, "text": s}]))
    assert ("/s (>" in out) is warns, out


def test_cjk_rules_match_craft_md():
    ct = load("check_timeline")
    assert ct.read_time("字" * 9) == pytest.approx(9 / 4.5 + 1.5)
    assert ct.read_time("字") == pytest.approx(1.5 + 1 / 4.5)
    assert ct.read_time("one two three four five six seven") == pytest.approx(1.0 + 0.3 * 7)
    assert ct.read_time("a") == 1.5


# ---- malformed input is reported, never a traceback

@pytest.mark.parametrize("bad, expected", [
    ("[1, 2]", "must be a JSON object"),
    ("{nope", "not valid JSON"),
    ('"text"', "must be a JSON object"),
    (film(meta="x"), "meta.w"),
    (film(meta={**film()["meta"], "clock": "music", "bpm": 0, "loop": True}), "bpm"),
    (film(meta={**film()["meta"], "clock": "music", "bpm": 120, "loop": True, "meter": "x"}), "meter"),
    (film(scenes="x"), "scenes must be a list"),
    (film(scenes=["x"]), "scenes"),
    (film(hero=6), "hero"),
    (film(vo={"status": "ESTIMATED"}), "vo must be a list"),
    (film(vo=[{"id": "L1", "words": "x"}]), "words"),
    (film(texts="x"), "texts must be a list"),
    (film(captions=[1]), "captions"),
    (film(silences=[1]), "silences"),
    (film(sfx=3), "sfx"),
    (film(reads=[1]), "reads"),
    (film(terms="bloom"), "terms must be a list"),
    (film(cuts=3), "cuts must be a list"),
])
def test_malformed_is_an_error_line(tmp_path, bad, expected):
    code, out = check(tmp_path, bad)
    assert code == 1 and expected in out, out


def test_missing_file(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPTS / "check_timeline.py"), str(tmp_path / "no.json")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "Traceback" not in r.stderr and "no.json" in r.stdout + r.stderr


def test_transition_as_a_string_warns(tmp_path):
    t = film()
    t["scenes"][0]["transitionOut"] = "cut"
    code, out = check(tmp_path, t)
    assert code == 0 and "no 'why'" in out


# ---- references and order

def test_text_pointing_at_a_missing_beat(tmp_path):
    t = film(texts=film()["texts"] + [{"text": "x", "in": "a.nope", "out": "a.y"}])
    code, out = check(tmp_path, t)
    assert code == 1 and "a.nope" in out


def test_text_named_by_beats_resolves(tmp_path):
    t = film(texts=film()["texts"] + [{"text": "x", "in": "a.x", "out": "a.y"}])
    assert check(tmp_path, t)[0] == 0


def test_list_beats_resolve_by_index(tmp_path):
    t = film()
    t["scenes"][0]["beats"] = [1, 3]
    t["texts"].append({"text": "x", "in": "a.0", "out": "a.1"})
    assert check(tmp_path, t)[0] == 0


def test_overlapping_scenes_warn(tmp_path):
    t = film()
    t["scenes"][1]["start"] = 3
    code, out = check(tmp_path, t)
    assert code == 0 and "overlaps" in out


def test_one_frame_overlap_is_fine(tmp_path):
    t = film()
    t["scenes"][1]["start"] = 5 - 1 / 60
    assert "overlaps" not in check(tmp_path, t)[1]


@pytest.mark.parametrize("sil, expected, code", [
    ({"from": 6, "to": 5}, "ends before it starts", 1),
    ({"from": 9, "to": 12}, "outside the film", 1),
])
def test_bad_silences(tmp_path, sil, expected, code):
    got, out = check(tmp_path, film(silences=[sil]))
    assert got == code and expected in out


def test_short_silence_warns_without_a_hero(tmp_path):
    t = film(silences=[{"from": 6, "to": 6.2}])
    del t["hero"]
    assert "under 0.4 s" in check(tmp_path, t)[1]


def test_text_after_the_end_is_an_error(tmp_path):
    t = film(texts=film()["texts"] + [{"text": "x", "from": 12, "to": 14}])
    code, out = check(tmp_path, t)
    assert code == 1 and "after the film ends" in out


# ---- the checks that already held

@pytest.mark.parametrize("edit, expected", [
    (lambda t: t.update(texts=[]), "no texts[] entry with role 'hook'"),
    (lambda t: t["texts"][0].update({"from": 3.5, "to": 8}), "first legible at 3.50"),
    (lambda t: t["texts"].append({"text": "go", "from": 4, "to": 6, "role": "cta", "px": 60}), "CTA first appears"),
    (lambda t: t["texts"][0].update(px=60), "below the 84 px floor"),
    (lambda t: t["scenes"][1].update(start=6), "gap"),
    (lambda t: t["scenes"][1].update(end=9), "scenes end at"),
    (lambda t: t["scenes"][1]["beats"].update(z=40), "outside the film"),
    (lambda t: t.update(sfx=[{"at": "a.nope"}]), "doesn't exist"),
])
def test_core_errors_hold(tmp_path, edit, expected):
    t = copy.deepcopy(film())
    edit(t)
    code, out = check(tmp_path, t)
    assert code == 1 and expected in out, out


def test_hook_waiver_downgrades(tmp_path):
    t = film(texts=[])
    t["meta"]["hookWaiver"] = "cold open, brief says so"
    t["terms"] = []
    code, out = check(tmp_path, t)
    assert code == 0 and "waived" in out


def test_px_floor_scales_with_resolution(tmp_path):
    t = film()
    t["meta"].update(w=1280, h=720)
    t["texts"][0]["px"] = 60  # 90 px at 1080
    assert check(tmp_path, t)[0] == 0


def test_music_loop_must_be_whole_bars(tmp_path):
    t = film()
    t["meta"].update(clock="music", bpm=120, loop=True, dur=10.1)
    t["scenes"][1]["end"] = 10.1
    code, out = check(tmp_path, t)
    assert code == 1 and "whole bars" in out


def test_floors_match_between_scripts(qa):
    ct = load("check_timeline")
    assert ct.TEXT_FLOORS == qa.TEXT_FLOORS


@pytest.mark.parametrize("s", ["布隆过滤器", "Bloom filter", "", "使用 AI 代码工具", "カタカナ"])
def test_is_cjk_matches_between_scripts(qa, s):
    assert load("check_timeline").is_cjk(s) is qa.is_cjk(s)
