# video-director

A Claude skill for making short videos written as code (HTML, Canvas, SVG, Three.js, GSAP or Remotion) and rendered frame by frame to MP4. It covers launch films, promos, explainers, data stories, kinetic type, character and illustrated shorts, loops and social reels.

The skill treats the model as a director: plan the film in numbers, build it deterministically, then measure what it can't watch or hear. It holds principles with their reasons, a workflow with a gate at each phase, and two QA scripts. It deliberately ships no shot library to copy.

## What's inside

| Path | What it is |
|---|---|
| [`video-director/SKILL.md`](video-director/SKILL.md) | The stance, the per-film dials (clock, continuity, register, text policy), 13 principles, the build contract, the brief structure and the definition of done |
| [`video-director/references/`](video-director/references/) | Templates (treatment, timeline, facts, delivery report), craft numbers, sound, the QA catalogue and critic rubric, and source credits |
| [`video-director/scripts/`](video-director/scripts/) | `check_timeline.py` validates the plan before any code; `qa_video.py` measures the render: hook text size and contrast, frame 0, flashes, cuts, freezes, loop seam, loudness, silences, contact sheets |
| [`video-director/evals/`](video-director/evals/) | Three test briefs with graders |
| [`METHODOLOGY.md`](METHODOLOGY.md) | The research the skill was distilled from: what drives quality across eight public repositories |

## Install

For Claude Code, copy the skill folder into your personal skills (or into a project's `.claude/skills/`):

```bash
git clone https://github.com/win4r/video-director.git
```

```bash
cp -R video-director/video-director ~/.claude/skills/
```

In the Claude apps, zip the inner `video-director/` folder and upload it as a custom skill.

The scripts need `ffmpeg`/`ffprobe` and Python 3 with `numpy` and `Pillow`. Rendering HTML films needs Node with Playwright and Chromium (or use Remotion). `faster-whisper` is optional, for checking narration, and any text-to-speech works for voice.

## Use

Ask for a video in plain words; the skill triggers on its own, even from a one-liner:

- "Make a 15 second looping launch video for our CLI. Everything you need is in the README."
- "I need a ~30 second narrated explainer on how a bloom filter works, 16:9."
- "A 20-second Reel from subscribers.csv for our public account. Keep it honest."

It also reviews and fixes existing coded videos ("this feels slow", "the text is unreadable"). You can run the checks yourself:

```bash
python3 video-director/scripts/check_timeline.py timeline.json
```

```bash
python3 video-director/scripts/qa_video.py film.mp4 --out qa/ --beats timeline.json
```

## Eval results

Each round ran the three briefs once per configuration. Script checks graded the measurable assertions; blind graders that didn't know which run was which graded the rest and picked the film they'd post.

| Round | Compared | Assertions passed | Blind preference | Cost |
|---|---|---|---|---|
| 1 | Skill vs no skill | 28/28 vs 25/28 | 2–1 for the skill | about 2× the time and tokens |
| 2 | Current skill vs round-1 skill | 30/32 vs 26/32 | 3–0 for the current skill | about the same |

Round 1 showed the skill catching craft basics (a black first frame, text under the Reels caption, quiet audio). It also showed two gaps: a tagline held back until 11 s, and an explainer that never said "false positive". Round 2 added the rules that fixed them. The hook and any call to action are on screen by 3 s with the sound off, at measured size and contrast. The terms the audience searches for are said and shown. Labels never sit on numbers that are still counting. With one run per configuration, treat these as a direction, not a measurement. The guidance for character and illustrated films, revisions and live pages was added after round 2 and hasn't been evaluated yet.

## Credits

The skill paraphrases and synthesizes the methodology of these public repositories; no file was copied. Each principle was reached independently by several of them. [`METHODOLOGY.md`](METHODOLOGY.md) has the evidence per principle, and [`sources.md`](video-director/references/sources.md) lists what each one contributed.

- [yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)
- [tuzhechen2005/opus-video-skills](https://github.com/tuzhechen2005/opus-video-skills)
- [whaleyxbt/claude-motion](https://github.com/whaleyxbt/claude-motion)
- [howseen-ai/claude-motion-design](https://github.com/howseen-ai/claude-motion-design)
- [AbubakrChan/product-launch-motion](https://github.com/AbubakrChan/product-launch-motion)
- [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)
- [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)
- [cth9191/animate](https://github.com/cth9191/animate)

The guidance for character and illustrated films, scoped revisions and live pages comes from the maintainer's own production notes on about 30 coded animation projects.

## License

[MIT](LICENSE)
