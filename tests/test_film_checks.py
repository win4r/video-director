"""Whole-film behaviour of qa_video.py, on films made from generated frames."""
import json
import subprocess
import sys

import numpy as np
import pytest

from conftest import SCRIPTS, ffmpeg, needs_ffmpeg, render, run_qa

pytestmark = needs_ffmpeg
W, H = 320, 180


def scene(i, seed=0, speed=2):
    """A textured frame that drifts sideways: real motion and contrast at every step."""
    x = (np.arange(W) + i * speed) % W
    y = np.arange(H)[:, None]
    grey = (127 + 90 * np.sin(x * 2 * np.pi / W * 3 + seed)[None, :] * np.cos(y * 2 * np.pi / H * 2 + seed)).astype(np.uint8)
    return np.dstack([grey, grey, grey])


def timeline(tmp_path, **extra):
    tl = {"meta": {"w": W, "h": H, "fps": 30, "dur": 3, "clock": "reads"}, "scenes": [{"id": "a", "start": 0, "end": 3}]}
    tl.update(extra)
    path = tmp_path / "t.json"
    path.write_text(json.dumps(tl))
    return path


@pytest.fixture
def plain(tmp_path):
    film = tmp_path / "plain.mp4"
    render(film, scene, 90)
    return film


def test_clean_film(plain, tmp_path):
    code, levels, _ = run_qa(plain, tmp_path / "qa")
    assert code == 0
    assert levels["frame 0"] == ["PASS"] and levels["single-frame flashes"] == ["PASS"]
    assert levels["audio"] == ["INFO"]
    for sheet in ("beats_sheet.jpg", "phone_sheet.jpg", "hook_sheet.jpg", "report.md"):
        assert (tmp_path / "qa" / sheet).exists()


def test_black_first_frame(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(i) * 0 if i == 0 else scene(i), 60)
    code, levels, _ = run_qa(film, tmp_path / "qa")
    assert code == 1 and levels["frame 0"] == ["FAIL"]


def test_single_frame_flash(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: np.full((H, W, 3), 255, np.uint8) if i == 40 else scene(i), 90)
    code, levels, report = run_qa(film, tmp_path / "qa")
    assert code == 1 and levels["single-frame flashes"] == ["FAIL"]
    assert report["picture"]["flashes"] == pytest.approx([40 / 30], abs=0.04)


def test_cut_on_plan(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(i, 3 if i >= 45 else 0) // (2 if i >= 45 else 1), 90)
    code, levels, report = run_qa(film, tmp_path / "qa", "--expect-cuts", "1.5")
    assert report["picture"]["cuts"] == pytest.approx([1.5], abs=0.04)
    assert levels["cuts vs plan"] == ["PASS"]


def test_cut_off_plan(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(i, 3 if i >= 45 else 0) // (2 if i >= 45 else 1), 90)
    code, levels, _ = run_qa(film, tmp_path / "qa", "--expect-cuts", "2.5")
    assert code == 1 and levels["cuts vs plan"] == ["FAIL"]


def test_freeze(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(min(i, 30) if i < 75 else i), 120)
    _, levels, report = run_qa(film, tmp_path / "qa")
    assert levels["frozen stretch"] == ["WARN"]
    fr = report["picture"]["frozen"][0]
    assert fr["from"] == pytest.approx(1.0, abs=0.07) and fr["to_end"] is False


def test_clean_loop(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(i, speed=5), 64)  # exactly one wrap: 64 x 5 = 320 px
    _, levels, report = run_qa(film, tmp_path / "qa", "--loop")
    assert levels["loop seam"] == ["PASS"], report["picture"]["loop"]


def test_jump_at_the_seam(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(i, speed=1), 60)
    code, levels, report = run_qa(film, tmp_path / "qa", "--loop")
    assert code == 1 and "FAIL" in levels["loop seam"], report["picture"]["loop"]


def test_last_frame_repeating_the_first_warns(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(i % 60, speed=W // 60), 61)
    _, levels, report = run_qa(film, tmp_path / "qa", "--loop")
    assert report["picture"]["loop"]["duplicate"] is True
    assert "WARN" in levels["loop seam"]


def test_still_loop_is_not_a_duplicate(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, lambda i: scene(0), 60)
    _, _, report = run_qa(film, tmp_path / "qa", "--loop")
    assert report["picture"]["loop"]["duplicate"] is False


# ---- render against plan

def test_render_matches_plan(plain, tmp_path):
    _, levels, _ = run_qa(plain, tmp_path / "qa", "--beats", timeline(tmp_path))
    assert levels["render vs plan"] == ["PASS"]


@pytest.mark.parametrize("meta, level, code", [
    ({"w": 180, "h": 320}, "FAIL", 1),     # portrait plan, landscape render
    ({"w": 640, "h": 360}, "WARN", 0),     # a half-size draft
    ({"fps": 60}, "WARN", 0),
    ({"dur": 5}, "WARN", 0),
])
def test_render_differs_from_plan(plain, tmp_path, meta, level, code):
    tl = timeline(tmp_path, meta={"w": W, "h": H, "fps": 30, "dur": 3, "clock": "reads", **meta})
    got, levels, _ = run_qa(plain, tmp_path / "qa", "--beats", tl)
    assert level in levels["render vs plan"] and got == code


def test_one_frame_short_of_plan_passes(tmp_path):
    film = tmp_path / "f.mp4"
    render(film, scene, 89)
    _, levels, _ = run_qa(film, tmp_path / "qa", "--beats", timeline(tmp_path))
    assert levels["render vs plan"] == ["PASS"]


def test_draft_scales_text_boxes(plain, tmp_path):
    tl = timeline(tmp_path, meta={"w": 640, "h": 360, "fps": 30, "dur": 3, "clock": "reads"},
                  texts=[{"text": "x", "from": 0.5, "role": "hook", "box": [100, 100, 200, 100]}])
    _, _, report = run_qa(plain, tmp_path / "qa", "--beats", tl)
    assert report["texts"][0]["box"] == [50, 50, 100, 50]


def test_bare_list_of_times_has_no_plan(plain, tmp_path):
    tl = tmp_path / "t.json"
    tl.write_text("[0.5, 1.5]")
    code, levels, _ = run_qa(plain, tmp_path / "qa", "--beats", tl)
    assert code == 0 and "render vs plan" not in levels


# ---- variable frame rate

def test_variable_frame_rate_warns_and_keeps_true_times(tmp_path):
    """ffmpeg repeats frames up to the nominal rate for rawvideo, so frame index still means time."""
    src = tmp_path / "src.mp4"
    render(src, lambda i: np.full((H, W, 3), 255, np.uint8) if i == 200 else scene(i), 300)  # flash at 6.67 s
    film = tmp_path / "vfr.mp4"
    ffmpeg("-i", src, "-vf", r"select='not(mod(n\,3))+between(n\,0\,30)+between(n\,195\,205)'", "-fps_mode", "vfr",
           "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", film)
    _, levels, report = run_qa(film, tmp_path / "qa")
    assert report["info"]["vfr"] is True
    assert levels["frame rate"] == ["WARN"]
    assert report["picture"]["flashes"] == pytest.approx([200 / 30], abs=0.1)


def test_constant_frame_rate_is_not_flagged(plain, tmp_path):
    _, levels, report = run_qa(plain, tmp_path / "qa")
    assert report["info"]["vfr"] is False and "frame rate" not in levels


@pytest.mark.parametrize("value, expected", [("30/1", 30.0), ("0/0", 0.0), ("30000/1001", 30000 / 1001)])
def test_rate(qa, value, expected):
    assert qa.rate(value) == pytest.approx(expected)


# ---- failures to run

def run_raw(*args):
    return subprocess.run([sys.executable, str(SCRIPTS / "qa_video.py"), *map(str, args)], capture_output=True, text=True)


@pytest.mark.parametrize("make", [lambda p: None, lambda p: p.write_bytes(b"not a video"), lambda p: p.write_text("")])
def test_unreadable_film_is_a_clean_exit_2(tmp_path, make):
    film = tmp_path / "bad.mp4"
    make(film)
    r = run_raw(film, "--out", tmp_path / "qa")
    assert r.returncode == 2 and "Traceback" not in r.stderr and "can't run" in r.stderr


@pytest.mark.parametrize("body", ["{nope", '"text"'])
def test_unreadable_timeline_is_a_clean_exit_2(plain, tmp_path, body):
    tl = tmp_path / "t.json"
    tl.write_text(body)
    r = run_raw(plain, "--out", tmp_path / "qa", "--beats", tl)
    assert r.returncode == 2 and "Traceback" not in r.stderr


@pytest.mark.parametrize("extra", [
    {"hero": 6}, {"hero": {"t": "later"}}, {"silences": [{"from": "a.x", "to": "a.y"}, 3]},
    {"cuts": 4}, {"texts": 3}, {"texts": [{"role": ["hook"]}, 3]}, {"scenes": ["x"]}, {"beats": "x"},
    {"meta": "x"}, {"texts": [{"text": "x", "from": 0.5, "role": "hook", "box": [0, 0, "w", 10]}]},
    {"texts": [{"text": "x", "from": 0.5, "role": "hook", "box": [0, 0, 0, 0]}]},
    {"texts": [{"text": "x", "from": 0.5, "role": "hook", "box": [900, 900, 10, 10]}]},
])
def test_malformed_timeline_fields_do_not_crash(plain, tmp_path, extra):
    code, levels, report = run_qa(plain, tmp_path / "qa", "--beats", timeline(tmp_path, **extra))
    assert report, "the run should still produce a report"
    assert code in (0, 1)


def test_box_outside_the_frame_says_so(plain, tmp_path):
    tl = timeline(tmp_path, texts=[{"text": "x", "from": 0.5, "role": "hook", "box": [900, 900, 10, 10]}])
    _, levels, report = run_qa(plain, tmp_path / "qa", "--beats", tl)
    assert levels["hook text"] == ["WARN"]
    assert any("outside the frame" in c["detail"] for c in report["checks"])


def test_list_beats_name_a_text_by_index(plain, tmp_path):
    tl = timeline(tmp_path, scenes=[{"id": "a", "start": 0, "end": 3, "beats": [0.5, 1]}],
                  texts=[{"text": "x", "in": "a.0", "role": "hook", "box": [10, 10, 100, 40]}])
    _, _, report = run_qa(plain, tmp_path / "qa", "--beats", tl)
    assert report["texts"][0]["from"] == 0.5


def test_short_planned_silence_is_reported_not_dropped(tmp_path):
    film = tmp_path / "f.mp4"
    ffmpeg("-f", "lavfi", "-i", f"testsrc2=s={W}x{H}:r=30:d=3", "-f", "lavfi", "-i", "sine=f=440:r=48000:d=3",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", film)
    tl = timeline(tmp_path, silences=[{"from": 1.0, "to": 1.05}])
    _, levels, _ = run_qa(film, tmp_path / "qa", "--beats", tl)
    assert levels["planned silence"] == ["WARN"]
