"""Shared helpers. The scripts are standalone files, so they are loaded by path."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "video-director" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def qa():
    return load("qa_video")


needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
                                  reason="ffmpeg/ffprobe not on PATH")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def render(path, frame, count, w=320, h=180, fps=30, extra=()):
    """Encode frame(i) -> uint8 RGB array to a near-lossless film."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", *map(str, extra),
                             "-c:v", "libx264", "-crf", "4", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                             str(path)], stdin=subprocess.PIPE)
    for i in range(count):
        proc.stdin.write(frame(i).tobytes())
    proc.stdin.close()
    assert proc.wait() == 0


def run_qa(video, out, *args):
    """Run qa_video.py as a user would. Returns (exit code, {check name: [levels]}, report)."""
    r = subprocess.run([sys.executable, str(SCRIPTS / "qa_video.py"), str(video), "--out", str(out),
                        *map(str, args)], capture_output=True, text=True)
    path = Path(out) / "report.json"
    report = json.loads(path.read_text(), parse_constant=_reject) if path.exists() else {}
    levels = {}
    for c in report.get("checks", []):
        levels.setdefault(c["check"], []).append(c["level"])
    return r.returncode, levels, report


def _reject(token):
    raise ValueError(f"report.json holds {token}, which is not valid JSON")
