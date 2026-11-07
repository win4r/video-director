import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from conftest import ffmpeg, needs_ffmpeg, run_qa

CJK_FONT = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")


def font(size):
    return ImageFont.load_default(size=size)  # Aileron, bundled with Pillow: same on every machine


def card(lines, size, leading=1.3, bg=(16, 16, 16), fg=(255, 255, 255), wide=1400):
    im = Image.new("RGB", (wide, int(40 + size * leading * len(lines) + size)), bg)
    draw = ImageDraw.Draw(im)
    for i, line in enumerate(lines):
        draw.text((20, 20 + i * size * leading), line, font=font(size), fill=fg)
    return im


def whole(im):
    return [0, 0, im.width, im.height]


@pytest.mark.parametrize("size", [40, 60, 84, 120])
def test_one_line_reads_near_its_set_size(qa, size):
    m = qa.measure_text(card(["Ship it today"], size), [0, 0, 1400, size * 2], 1080)
    assert m["font_px"] == pytest.approx(size, rel=0.1)
    assert m["lines"] == 1


@pytest.mark.parametrize("leading", [1.0, 1.05, 1.1, 1.2, 1.3, 1.5])
@pytest.mark.parametrize("size", [40, 60])
def test_display_leading_does_not_inflate_a_block(qa, leading, size):
    """A 60 px hook set solid must not clear the 84 px floor."""
    im = card(["Happy typing", "Gently jumping", "Quietly glowing"], size, leading)
    m = qa.measure_text(im, whole(im), 1080)
    assert m["font_px"] == pytest.approx(size, rel=0.15)
    assert m["lines"] == 3


@pytest.mark.parametrize("lines, leading", [
    (["HELLO WORLD", "SECOND LINE", "THIRD LINE"], 1.5),
    (["Happy typing", "Gently jumping", "Quietly glowing"], 1.3),
    (["Happy typing", "Gently jumping", "Quietly glowing"], 1.1),  # descenders meet ascenders
])
def test_block_of_small_lines_is_not_one_big_line(qa, lines, leading):
    im = card(lines, 40, leading)
    m = qa.measure_text(im, whole(im), 1080)
    assert m["font_px"] == pytest.approx(40, rel=0.15)
    assert m["lines"] == 3


@pytest.mark.parametrize("text", ["EEEEEE", "EFFECT", "mini nimi", "Tumnu"])
def test_one_line_is_not_split_by_its_own_letters(qa, text):
    """Rows between the bars of an E are sparse, and the dot of an i floats free."""
    m = qa.measure_text(card([text], 100), [0, 0, 1400, 200], 1080)
    assert m["lines"] == 1


@pytest.mark.parametrize("text", ["TTTTTT", "TILT", "HELLO", "FFFFFF", "Ship it", "Quietly"])
def test_one_line_near_set_size_whatever_the_letters(qa, text):
    """A top-heavy T must not lift the baseline; descenders must not lower it."""
    m = qa.measure_text(card([text], 100), [0, 0, 1400, 200], 1080)
    assert m["font_px"] == pytest.approx(100, rel=0.2)


@pytest.mark.parametrize("text", ["gypsy jumping", "ggg jjj"])
def test_descender_heavy_line_stays_within_a_third(qa, text):
    """A known limit, pinned: with descenders everywhere, one line reads up to ~28% high."""
    m = qa.measure_text(card([text], 100), [0, 0, 1400, 200], 1080)
    assert 100 <= m["font_px"] <= 133


def test_small_kicker_above_a_big_title_is_its_own_line(qa):
    im = Image.new("RGB", (1400, 300), (16, 16, 16))
    draw = ImageDraw.Draw(im)
    draw.text((20, 10), "KICKER", font=font(36), fill="white")
    draw.text((20, 90), "HUGE", font=font(120), fill="white")
    m = qa.measure_text(im, whole(im), 1080)
    assert m["font_px"] == pytest.approx(120, rel=0.1)
    assert m["lines"] == 2


def test_tight_kicker_does_not_cap_the_big_title_below_it(qa):
    """Line spacing limits lines of a similar size, not a small line sitting close above a big one."""
    im = Image.new("RGB", (1400, 240), (16, 16, 16))
    draw = ImageDraw.Draw(im)
    draw.text((20, 4), "KICKER", font=font(36), fill="white")
    draw.text((20, 26), "HUGE", font=font(120), fill="white")
    m = qa.measure_text(im, whole(im), 1080)
    assert m["lines"] == 2
    assert m["font_px"] == pytest.approx(120, rel=0.1)  # capped at the spacing, it would read ~103


def test_largest_line_counts(qa):
    im = Image.new("RGB", (1400, 300), (16, 16, 16))
    draw = ImageDraw.Draw(im)
    draw.text((20, 10), "HUGE", font=font(120), fill="white")
    draw.text((20, 190), "SMALL PRINT", font=font(40), fill="white")
    m = qa.measure_text(im, whole(im), 1080)
    assert m["font_px"] == pytest.approx(120, rel=0.1)
    assert m["lines"] == 2


def test_scales_to_a_1080_short_side(qa):
    im = card(["Ship it"], 40)
    assert qa.measure_text(im, whole(im), 720)["font_px"] == pytest.approx(60, rel=0.1)


@pytest.mark.parametrize("grey", [0, 10, 16, 20, 30])
def test_hard_edged_glyphs_on_near_black(qa, grey):
    """With no anti-aliasing the histogram has two bins, and the split must fall between them."""
    im = Image.new("RGB", (400, 120), (grey, grey, grey))
    draw = ImageDraw.Draw(im)
    for x in range(20, 380, 30):
        draw.rectangle([x, 20, x + 10, 99], fill=(255, 255, 255))
    m = qa.measure_text(im, whole(im), 1080)
    assert m["font_px"] == pytest.approx(80 / 0.72, abs=2)
    assert m["contrast"] > 10


def test_dark_text_on_light(qa):
    im = card(["Ship it"], 100, bg=(245, 245, 245), fg=(10, 10, 10))
    m = qa.measure_text(im, whole(im), 1080)
    assert m["font_px"] == pytest.approx(100, rel=0.1) and m["contrast"] > 10


def test_flat_crop_measures_nothing(qa):
    m = qa.measure_text(Image.new("RGB", (200, 100), (40, 40, 40)), [0, 0, 200, 100], 1080)
    assert m["font_px"] == 0.0 and m["contrast"] == 1.0


def test_box_past_the_frame_measures_the_frame_not_padding(qa):
    im = Image.new("RGB", (400, 200), (255, 255, 255))
    ImageDraw.Draw(im).text((300, 120), "Hi", font=font(40), fill=(120, 120, 120))
    m = qa.measure_text(im, [290, 110, 300, 200], 1080)
    assert m["clipped"] is True
    assert m["contrast"] < 5  # black padding would read as ~20:1
    assert m["font_px"] < 60


def test_rounding_past_the_edge_is_not_clipping(qa):
    im = card(["Ship it"], 100)
    assert qa.measure_text(im, [0, 0, im.width + 1, im.height + 1], 1080)["clipped"] is False


@pytest.mark.parametrize("box", [[5000, 0, 100, 100], [0, 0, 0, 0], [0, 0, -5, 10]])
def test_box_outside_the_frame_is_unmeasured(qa, box):
    assert qa.measure_text(card(["x"], 40), box, 1080) == {}


@pytest.mark.parametrize("text, ratio", [
    ("布隆过滤器", 0.92), ("日本語のテキスト", 0.92), ("데이터", 0.92), ("ｶﾀｶﾅ", 0.92),
    ("增长300%", 0.92), ("TypeScript 类型系统入门", 0.92),  # one CJK glyph sets the line's height
    ("Bloom filter", 0.72), ("", 0.72), ("123", 0.72), ("HELLO", 0.72),
    ("scan a room now", 0.52), ("gypsy", 0.52),  # x-height only
])
def test_glyph_ratio(qa, text, ratio):
    assert qa.glyph_ratio(text) == ratio


def test_x_height_text_reads_at_its_set_size(qa):
    m = qa.measure_text(card(["scan a room now"], 100), [0, 0, 1400, 200], 1080, "scan a room now")
    assert m["font_px"] == pytest.approx(100, rel=0.15)


SERIF_LINE = [0, 11, 41, 56, 59, 58, 60, 62, 60, 58, 54, 48, 42, 35, 35] + [24] * 12 + [84, 214, 237, 248, 219, 204, 143] \
    + [125] * 40 + [162, 204, 277, 262, 242, 28, 0]  # Georgia 96 px, "this is fine": ascenders above a gap


@pytest.mark.parametrize("rows, lines", [
    ([0, 80, 80] + [8] * 9 + [80, 80, 0], 1),  # serifs alone: thin rows, wide valley
    (SERIF_LINE, 1),
    (SERIF_LINE + SERIF_LINE, 2),
    ([0, 80] + [90] * 20 + [8] * 4 + [90] * 20 + [80, 0], 2),  # tight leading: tall bands, thin valley
    ([0] + [100] * 30 + [40] * 8 + [0], 1),  # a descender zone stays with its line
    ([0] + [90] * 30 + [0] * 3 + [90] * 4 + [0], 1),  # an underline just below is not a line
    ([0] + [90] * 5 + [0] * 3 + [90] * 30 + [0], 1),  # nor is the dot of an i above
    ([0] + [90] * 10 + [0] * 20 + [90] * 30 + [0], 2),  # a far-off small line is
])
def test_line_bands_on_profiles(qa, rows, lines):
    assert len(qa.line_bands(np.array(rows))) == lines


def test_underline_is_not_part_of_the_line(qa):
    im = card(["Ship it"], 70)
    ImageDraw.Draw(im).rectangle([20, 100, 400, 105], fill="white")
    m = qa.measure_text(im, [0, 0, 1400, 130], 1080)
    assert m["font_px"] == pytest.approx(70, rel=0.15)
    assert m["lines"] == 1


def test_negative_leading_is_capped_at_the_line_spacing(qa):
    im = card(["Happy typing", "Gently jumping", "Quietly glowing"], 90, 0.9, wide=1600)
    assert qa.measure_text(im, whole(im), 1080)["font_px"] == pytest.approx(90, rel=0.05)


def test_small_subtitle_doesnt_stretch_the_title(qa):
    im = Image.new("RGB", (1400, 200), (16, 16, 16))
    draw = ImageDraw.Draw(im)
    draw.text((20, 10), "Big title", font=font(70), fill="white")
    draw.text((20, 94), "a small subtitle", font=font(24), fill="white")
    assert qa.measure_text(im, whole(im), 1080)["font_px"] == pytest.approx(70, rel=0.15)


SERIFS = [Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
          Path("/System/Library/Fonts/Supplemental/Georgia.ttf")]


@pytest.mark.parametrize("path", [p for p in SERIFS if p.exists()] or [None], ids=lambda p: p.name if p else "none")
@pytest.mark.parametrize("text", ["this is fine", "Why your hiring is slow"])
def test_one_serif_line_is_one_line(qa, path, text):
    if path is None:
        pytest.skip("no serif font here")
    im = Image.new("RGB", (1400, 200), (0, 0, 0))
    ImageDraw.Draw(im).text((20, 20), text, font=ImageFont.truetype(str(path), 96), fill="white")
    m = qa.measure_text(im, whole(im), 1080, text)
    assert m["lines"] == 1
    assert m["font_px"] == pytest.approx(96, rel=0.25)


def test_cjk_uses_a_taller_glyph_ratio(qa):
    im = card(["Ship it"], 100)
    latin = qa.measure_text(im, whole(im), 1080, "Ship it")
    cjk = qa.measure_text(im, whole(im), 1080, "布隆过滤器")
    assert cjk["font_px"] == pytest.approx(latin["font_px"] * 0.72 / 0.92, abs=0.2)


@pytest.mark.skipif(not CJK_FONT.exists(), reason="needs a macOS CJK font")
def test_70px_chinese_hook_stays_under_the_84px_floor(qa):
    im = Image.new("RGB", (900, 160), (10, 10, 30))
    ImageDraw.Draw(im).text((10, 10), "布隆过滤器原理", font=ImageFont.truetype(str(CJK_FONT), 70), fill="white")
    m = qa.measure_text(im, whole(im), 1080, "布隆过滤器原理")
    assert m["font_px"] == pytest.approx(70, rel=0.08)


@pytest.mark.parametrize("box, ok", [
    ([0, 0, float("nan"), 10], False), ([0, 0, float("inf"), 10], False),
    ([0, 0, 10, 10], True), ([0.5, 1, 2.5, 3], True), ([0, 0, 10], False), (None, False),
    ([0, 0, "a", 10], False), ([0, 0, True, 10], False),
])
def test_valid_box(qa, box, ok):
    assert qa.valid_box(box) is ok


@needs_ffmpeg
def test_three_small_lines_fail_the_hook_floor_on_a_real_render(tmp_path):
    """The whole path: PNG card, H.264 render, timeline, report."""
    im = Image.new("RGB", (1080, 1080), (16, 16, 18))
    draw = ImageDraw.Draw(im)
    for i, line in enumerate(["SMALL HOOK", "ON THREE", "LINES HERE"]):
        draw.text((100, 200 + i * 70), line, font=font(40), fill="white")
    im.save(tmp_path / "card.png")
    film = tmp_path / "film.mp4"
    ffmpeg("-loop", "1", "-i", tmp_path / "card.png", "-t", "2", "-r", "30",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", film)
    timeline = tmp_path / "t.json"
    timeline.write_text(json.dumps({
        "meta": {"w": 1080, "h": 1080, "fps": 30, "dur": 2, "clock": "reads"},
        "scenes": [{"id": "a", "start": 0, "end": 2}],
        "texts": [{"text": "SMALL HOOK ON THREE LINES HERE", "from": 0.2, "to": 2, "role": "hook",
                   "box": [90, 190, 600, 240]}]}))
    code, levels, report = run_qa(film, tmp_path / "qa", "--beats", timeline)
    assert levels["hook text"] == ["FAIL"], report["texts"]
    assert code == 1
