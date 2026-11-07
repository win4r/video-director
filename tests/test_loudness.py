import math
import re

import pytest

from conftest import ffmpeg, needs_ffmpeg, run_qa


@pytest.mark.parametrize("lufs, peak, level", [
    (-14.0, -1.0, "PASS"),
    (-14.0, -1.1, "PASS"),
    (-14.0, -0.9, "FAIL"),
    (-14.0, 0.0, "FAIL"),   # issue 1: 0.0 is falsy
    (-14.0, 0.8, "FAIL"),
    (-14.0, -math.inf, "PASS"),
    (-16.0, -3.0, "FAIL"),  # too quiet
    (-12.0, -3.0, "FAIL"),  # too loud
    (None, -3.0, "WARN"),   # unmeasured is not a pass
    (-14.0, None, "WARN"),
    (None, None, "WARN"),
    (-20.0, None, "FAIL"),  # what was measured already fails
    (None, 0.0, "FAIL"),
])
def test_loudness_verdict(qa, lufs, peak, level):
    assert qa.loudness_verdict(lufs, peak, -14.0, -1.0)[0] == level


def test_verdict_names_what_is_unmeasured(qa):
    assert "true peak" in qa.loudness_verdict(-14.0, None, -14.0, -1.0)[2]
    assert "LUFS" in qa.loudness_verdict(None, -3.0, -14.0, -1.0)[2]


@needs_ffmpeg
def test_full_scale_film_fails_on_true_peak(tmp_path):
    """Issue 1 end to end: a measured true peak of exactly 0.0 dBTP, otherwise on target."""
    film = tmp_path / "peak.mkv"
    ffmpeg("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=4",
           "-f", "lavfi", "-i", "aevalsrc='if(lt(mod(t,1),0.2),sin(2*PI*1000*t),0.21*sin(2*PI*1000*t))':s=48000:d=4",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le", film)
    _, levels, report = run_qa(film, tmp_path / "qa", "--lufs", "-9.6", "--tp", "-1")
    assert report["audio"]["true_peak"] == 0.0
    assert abs(report["audio"]["lufs"] + 9.6) <= 1.0  # so only the true peak can fail this film
    assert levels["loudness"] == ["FAIL"], report["audio"]


@needs_ffmpeg
def test_silent_track_leaves_valid_json(tmp_path):
    """-inf dBTP must not reach report.json: Infinity is not JSON."""
    film = tmp_path / "silent.mp4"
    ffmpeg("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=2", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", film)
    _, levels, report = run_qa(film, tmp_path / "qa")  # the helper rejects Infinity/NaN
    assert report["audio"]["true_peak"] is None
    assert levels["loudness"] == ["FAIL"]
    assert re.search(r"-inf", next(c for c in report["checks"] if c["check"] == "loudness")["detail"])
