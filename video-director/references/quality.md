# Quality: checks, tells, critique, traps

Automated gates catch what is *broken*, not what is *bad*. Run them first so the visual review and the critic can spend their attention on judgment. Review happens in three layers:
1. Numeric checks while building.
2. Visual review of stills and strips.
3. An independent critic.

## Contents
1. Check catalogue (what, how, what it catches)
2. Visual review protocol
3. The AI-tells list (banned defaults)
4. Independent critic: brief and rubric
5. Failure → fix table
6. Iteration discipline

---

## 1. Check catalogue

| Check | How | Catches | Pass |
|---|---|---|---|
| Timeline | `scripts/check_timeline.py` before any code and after any retime | Gaps between scenes; beats outside the film; loops that aren't whole bars; SFX pointing at missing beats; hero spent early; no silence before it; reads and captions too short; ESTIMATED VO | 0 errors; every warning resolved or deliberate |
| Determinism | Render a set of frames forward, then in reverse order, and diff them | Hidden state, unseeded RNG, timers | Identical pixels |
| Page errors | Capture the console and page errors during render; abort on any | Silent JS failures, missing assets | Zero |
| Fonts/assets ready | Await `READY` / `document.fonts.ready` before the first capture | Fallback fonts and half-loaded images in early frames | Fonts present in frame 0 |
| Read time | Sample `TEXTS(t)` every frame; measure how long each string stays fully visible | Text cut before it can be read; text never fully in frame | Every string ≥ its formula (craft.md §2) |
| Text bounds | Trace `fillText` and DOM boxes into screen space | Cropped, overlapping or under-UI text (it looks fine at thumbnail size) | Inside the safe area, no overlaps |
| Phone legibility | Contact sheet at 360 px wide | Text too small for a phone feed | Every read is legible |
| Frame 0 | Luminance and contrast of the first frame | Black or blank thumbnails, and half-built first compositions | Not flat; looks finished |
| Pops / flashes | Frame-difference spike > 3× both neighbours; flash: n−1 ≈ n+1 while n differs | One-frame glitches, stray transitions, chunk seams, crashed retries | Zero, or each one explained as an intended cut |
| Frozen stretches | Runs of near-zero frame difference | Dead air, unintended stalls | Each one is a designed hold |
| Flat frames | Frames with very low contrast mid-film | Blank frames inside transitions | Zero |
| Cuts vs plan | Detected cuts compared with the timeline's cut list | Cuts that drift off the beat or word | ≤ 1 frame |
| Beat sync (rendered) | Re-fit the grid on the rendered audio and compare it with picture cuts | Sync that drifts or shifts after the encode | ≤ 3 frames (≤ 1.5 ideal) |
| Loudness | ebur128 on the delivered file | Too quiet, too loud, clipped master | −14 LUFS ±1, TP ≤ −1 dBTP |
| Dramatic arc | Loudest 100 ms; silences (definition in sound.md §5); planned silences measured | Payoff not loudest; no silence before it; a planned silence that is really a quiet bed | Loudest moment on the payoff (for a voice clock: the loudest non-voice hit, in a VO pause); a silence precedes it; every planned silence is actually silent |
| Loop seam | Last→first difference vs the median step; speed going into frame 0 vs speed coming out | Loops that match in position but jump in momentum | Seam ≤ 2× median (or < 0.5/255 when the film is mostly still); speed ratio 0.5–2 |
| Anchor stability | Track the hero's screen position | A hero that drifts in the fast section | ≥ 95% of frames within ~40 px of its anchor |
| ASR on VO | Whisper on each TTS line and on the final mix | Mispronunciations, garbled numbers | Matches the script |
| Resolution | Source pixels per screen pixel for every image | Upscaled mush | ≥ 1 for photos |
| Facts | Every on-screen number and claim traced to a FACTS.md row | Invented or overstated claims | 100% traced or labelled |
| Leaks | Grep committed files and rendered text for process words, placeholders ("Acme", "lorem", "Your headline"), debug labels, card names | Template residue | Zero; also *watch the last seconds*, because text drawn into images can't be grepped |

`scripts/qa_video.py` covers frame 0, pops/flashes, frozen and flat frames, cuts vs plan, loudness, dramatic arc, loop seam and the contact sheets. The page-level checks (determinism, read time, text bounds) need the page contract (craft.md §12).

## 2. Visual review protocol

**Sheets and strips to make:**
- **Beat sheet:** one frame per timeline beat, taken **0.3 s after** the beat, once motion has settled. If a tile from the middle of a hold still shows text animating, the hold is too short.
- **Overview sheet:** 1–2 fps, tiled about 6×5, for rhythm and variety.
- **Strips:** every frame (or every 0.1–0.2 s) across each transition, each fast move and each key action. Check for anticipation, twinning, landings, overlaps during swaps, and blank frames.
- **Phone sheet:** 1 fps at 360 px wide.
- **Per shot:** at least the first and last 0.5 s, and three acceptance frames (mid-entrance, action peak, after the settle).
- **Full resolution:** for judging scale, faces and text edges. Contact sheets mislead about how big things are.

**Review in passes, one class of problem per pass:**
1. Sync: pick five random reveals and check each against its cue.
2. Motion: the strips, with the audio ignored.
3. One full read top to bottom: what do you remember?

**Before showing the user anything,** have the review done by someone other than the builder (§4). The user should never be the first viewer.

## 3. The AI-tells list (banned defaults)

These are what a model produces when unconstrained. Ban them unless the brief deliberately asks for one, and say so if it does.

**Composition**
- A centred title on a gradient.
- Corner labels, frame borders, HUD chrome: timecodes, progress counters, "SCENE 01". Honesty labels such as `SCHEMATIC` are not chrome; they sit on the graphic they qualify (craft.md §11).
- Crowded vertical stacks.
- A tiny subject in an empty frame.
- A final frame that isn't a poster.

**Motion**
- Everything fades in; opacity-only entrances.
- Everything moving at once, on one curve, for one duration.
- Linear easing on anything that starts or stops.
- Bouncy or cartoon easing in serious registers.
- Gratuitous 3D flips.
- Handheld shake in product films.
- The camera pumping on every beat.
- Settles that move in 3-frame steps.

**Look**
- Glows, lens flares and particle bursts.
- Rainbow gradients, or one indigo used everywhere.
- Decorative glints on every element, or glow leaking past rounded corners.
- An unlit flat stage with a dead background.
- The model's default font.
- Emoji as illustration.

**Content**
- Grey placeholder UI and skeleton bars.
- "Acme", lorem ipsum, "Your headline here".
- A technique described in text (a "FREEZE" badge) instead of shown.
- A sign that repeats what the picture already says.
- Fake UI "mockup + slogan".
- Invented features or numbers.

**Structure**
- A slow logo reveal as the opening.
- A logo sting as the only ending.
- Crossfades and generic wipes.
- Every shot an unlinked world.
- One even speed throughout.

**Sound**
- Noise whooshes on every cut.
- Game-pack bleeps.
- A sound on every motion.
- Generic "piano and strings" in place of the style's own instrument palette.

## 4. Independent critic: brief and rubric

**Spawn a fresh subagent** that never saw the build or its reasoning. Give it:
- the rendered file, or the sheets and strips;
- the brief or treatment;
- the timeline;
- FACTS.md;
- this rubric.

If an input is missing, the critic marks the affected items "unverifiable" rather than guessing. When two sources conflict, it reports the conflict instead of resolving it quietly.

**Critic brief (adapt):**

> You are a harsh motion director reviewing a film you did not make. Default to reject.
>
> 1. From the frames alone, state the film's message in one sentence. Then compare it with the brief's intended sentence.
> 2. Score each axis 1–10, with evidence: frame or timestamp, and what you see.
> 3. List the defects ranked P0 (must fix) / P1 / P2. Each gets a timestamp, the symptom, the likely mechanism, and a *measurable* fix.
> 4. End with "ship" or "one more pass", and the single weakest shot.
>
> Don't write "looks good overall" without evidence, and don't mark everything as passing.

**Axes:**

| Axis | Look for |
|---|---|
| Hook | First read lands within 2–3 s; frame 0 finished |
| Clarity | One idea; the muted one-sentence test; reads given enough time |
| Readability | 360 px legibility; holds; no overprinting during swaps |
| Motion quality | Easing by role, weight, anticipation, no twinning, landings |
| Rhythm and variety | Cued reveals; acceleration plus a breath; no dead or flat stretches; new information every 2–4 s |
| Composition and look | One focal point, light and depth, accent discipline, poster holds, none of the tells |
| Continuity | A motivated transition on every seam; persistent objects; no repeated adjacent camera moves |
| Truth | Numbers traced; labels present; real UI |
| Sound sync | Hits on picture events; silence before the payoff; loudest on the payoff (from the measurements) |

**Bar:** ship when every axis scores 8 or more and there are no P0 defects.

**One-round fixing:**
- Fix the shots scored 7 or below.
- Leave the shots scored 9 or above alone, to avoid regressions.

**Versions:**
- A new version replaces the old one only if a side-by-side comparison judges it better.

## 5. Failure → fix table

| Symptom | Likely mechanism | Fix |
|---|---|---|
| "Feels like a slideshow" | One stagger at the shot start, then a freeze; reveals cued to nothing | Cue each element to a beat, word or read; weight arrivals to the back half; give the shot more than one event |
| "Busy but nothing lands" | The screensaver: endless independent loops | Bound every move; let one element keep life; end motion before the cut |
| "Too fast" (the most common note) | Reads overlapping; holds under the formula | Add hold time; cut words per screen; one read at a time |
| "Cheap" | Linear timing, opacity-only entrances, flat unlit stage, small text | Easing by role with travel, a light on the hero, layered depth, bigger type |
| "Generic / AI-looking" | Default tells (§3); no benchmark | Name the benchmark; apply the banned list; one central formal idea |
| Text blurry in motion | Scaled raster, `will-change` on scaled layers, blur on read text | Rasterize at 2–4×; remove `will-change`; take read text out of the blur |
| Text overlapping during a swap | Old and new text share one window | Give each its own enter and exit windows; exit short and early |
| Subject drops under the caption on zoom | Zooming about a point | Map a world point to a screen point |
| The click feels lost | Camera still moving during the click | Settle the camera before the action; zoom origin on the control |
| Jitter in fast sections | Unseeded RNG or carried state; camera animated on twos | Seed everything; derive from `t`; keep the camera smooth every frame |
| A fix that doesn't stick between renders | Something is non-deterministic | Render out of order and diff; remove timers and transitions |
| A hit sounds early or late | Aligned by file start; encoder delay | Align by measured peak; measure the output offset once and apply it as a constant |
| Cue inaudible | Quiet source; window peak passed it | Level the asset; check the 100 ms envelope |
| Payoff doesn't land | No silence before it; busiest section louder | Add a 0.4–4 s drop; put the loudest hit on the payoff; reduce density just before |
| Whooshes annoying | A sound on every cut | Silence half the cuts; vary the cues; save impacts for structure |
| Morph turns to mud | Blending two saturated grounds | Morph through a neutral |
| Loop stutters | Position matches but velocity jumps | Wrap time; match speed into and out of frame 0 |
| Same film as last time | Structure inherited from an example | Treatment before opening any example; three structures; the 4-of-6 difference check |
| Blank frames at a transition | Scene drawn at negative local time | Clamp local `t`; the next scene enters already moving |
| Invented claim slipped in | No facts gate | FACTS.md; trace every number before the final render |

## 6. Iteration discipline

- **A note is a symptom report, not a spec.** Translate it into the mechanism behind it before touching code. "Make it 3D" turned out to mean a camera rig plus a coordinate refactor.
- **One change per commit,** so a misread note can be reverted cleanly. Version every render, and keep the raw files of endings people liked.
- **After the critic: one fix round, then one re-check.** Unbounded loops make different things worse, not things better.
- **Don't claim a fix you haven't re-rendered and looked at.** Report what was checked, what was fixed, and which sheet shows it.
- **Report honestly:**
  - which numbers are real and which are illustrative;
  - whether the audio was measured or heard;
  - which shot is weakest;
  - what you would fix next;
  - which likenesses or logos need permission.
