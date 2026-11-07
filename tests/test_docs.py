"""The skill's text is its product: its pointers and numbers are tested like code."""
import re
from pathlib import Path

import pytest

from conftest import ROOT, load

SKILL = ROOT / "video-director"
READMES = [ROOT / "README.md", ROOT / "README.zh-CN.md", ROOT / "README.ja.md"]
DOCS = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]


def frontmatter():
    text = (SKILL / "SKILL.md").read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(line.split(": ", 1) for line in m.group(1).splitlines())


def test_frontmatter_is_loadable():
    fm = frontmatter()
    assert set(fm) == {"name", "description"}
    assert re.fullmatch(r"[a-z0-9-]{1,64}", fm["name"])
    assert fm["name"] == SKILL.name
    assert 0 < len(fm["description"]) <= 1024
    assert "<" not in fm["description"]


def test_skill_body_stays_lean():
    assert (SKILL / "SKILL.md").read_text().count("\n") < 500


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_named_files_exist(doc):
    missing = []
    for path in re.findall(r"`?((?:references|scripts|evals)/[\w./-]+\.\w+)`?", doc.read_text()):
        if not (SKILL / path).exists():
            missing.append(path)
    assert not missing


def sections(path):
    """Every 'N' in a '## N. Title' heading."""
    return set(re.findall(r"^#+ (\d+)\.", path.read_text(), re.M))


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_section_references_resolve(doc):
    refs = re.findall(r"(?:references/)?(\w+)\.md`? §(\d+)(?:[–-](\d+))?", doc.read_text())
    assert doc.name != "SKILL.md" or refs
    for name, first, last in refs:
        target = SKILL / "references" / f"{name}.md"
        if name == "SKILL":
            continue
        assert target.exists(), name
        for n in range(int(first), int(last or first) + 1):
            assert str(n) in sections(target), f"{doc.name} points at {name}.md §{n}"


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_skill_doesnt_lean_on_files_that_wont_ship(doc):
    """Only video-director/ is installed, so a pointer outside it has to say where it leads."""
    for line in doc.read_text().splitlines():
        assert "METHODOLOGY.md" not in line or "repository" in line


def test_principle_references_exist():
    skill = (SKILL / "SKILL.md").read_text()
    numbers = {int(n) for n in re.findall(r"^\*\*(\d+)\. ", skill[skill.index("## Principles"):], re.M)}
    assert numbers == set(range(1, 14))  # the README says 13
    for doc in DOCS:
        for n in re.findall(r"principle (\d+)", doc.read_text(), re.I):
            assert int(n) in numbers, f"{doc.name}: principle {n}"


# ---- numbers quoted in the docs match the scripts

def test_floors_in_prose_match_code(qa):
    skill = (SKILL / "SKILL.md").read_text()
    assert f"hook ≥ {qa.TEXT_FLOORS['hook']}" in skill
    assert f"CTA and key terms ≥ {qa.TEXT_FLOORS['cta']}" in skill
    assert f"≥ {qa.MIN_CONTRAST:g}:1" in skill


def test_hook_deadline_in_prose_matches_code():
    assert load("check_timeline").HOOK_BY == 3.0
    assert "by 3 s" in (SKILL / "SKILL.md").read_text()


def test_caption_limits_in_prose_match_code():
    ct = load("check_timeline")
    craft = (SKILL / "references" / "craft.md").read_text()
    assert f"≤ {ct.CAPTION_WPS:g} words/s" in craft
    assert f"≤ {ct.CAPTION_CJK_CPS:g} characters/s" in craft


def test_loudness_defaults_match_prose():
    source = (SKILL / "scripts" / "qa_video.py").read_text()
    assert 'add_argument("--lufs", type=float, default=-14.0)' in source
    assert 'add_argument("--tp", type=float, default=-1.0' in source
    assert "−14 LUFS ±1 and true peak ≤ −1 dBTP" in (SKILL / "SKILL.md").read_text()


def test_timeline_fields_qa_reads_are_documented():
    briefs = (SKILL / "references" / "briefs.md").read_text()
    for field in ('"cuts"', '"silences"', '"hero"', '"texts"', '"terms"', '"captions"', '"vo"', '"sfx"'):
        assert field in briefs


# ---- READMEs

@pytest.mark.parametrize("readme", READMES, ids=lambda r: r.name)
def test_readme_links_resolve(readme):
    text = readme.read_text()
    for link in re.findall(r"\]\((?!https?://)([^)#]+)\)", text):
        assert (ROOT / link).exists(), link


@pytest.mark.parametrize("readme", READMES, ids=lambda r: r.name)
def test_language_switcher_is_complete(readme):
    line = next(l for l in readme.read_text().splitlines() if "English" in l and "简体中文" in l)
    assert "日本語" in line
    for other in READMES:
        if other != readme:
            assert f"]({other.name})" in line


def outline(readme):
    text = readme.read_text()
    return {"headings": [len(h) for h in re.findall(r"^(#+) ", text, re.M)],
            "code": re.findall(r"```bash\n(.*?)```", text, re.S),
            "numbers": re.findall(r"\d+/\d+", text),
            "links": sorted(re.findall(r"\]\(([^)]+)\)", re.sub(r".*English.*\n", "", text)))}


@pytest.mark.parametrize("readme", READMES[1:], ids=lambda r: r.name)
def test_translations_track_the_english_readme(readme):
    assert outline(readme) == outline(READMES[0])


# ---- evals

CASES = sorted(p.parent for p in (SKILL / "evals").glob("*/case.yaml"))


def test_three_evals_as_the_readme_says():
    assert len(CASES) == 3


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_eval_case_is_complete(case):
    yaml = (case / "case.yaml").read_text()
    assert f"name: {case.name}" in yaml
    assert (case / "prompt.md").read_text().strip()
    scaffold = re.search(r"scaffold_script: (\S+)", yaml)
    if scaffold:
        assert (case / scaffold.group(1)).exists()
    graders = sorted((case / "graders").glob("*.md"))
    numbers = [int(g.name.split("-")[0]) for g in graders]
    assert numbers == list(range(1, len(graders) + 1))
    assert all(g.read_text().strip() for g in graders)
