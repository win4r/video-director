# Craft: numbers, presets and engineering

Every number in this file is a **default you deviate from on purpose**. Where the source projects disagreed, the range is given and the register decides. Where a value came from a single production, it is marked *(single case)*.

All values assume a canvas whose short side is 1080 px. Scale them proportionally for other sizes.

## Contents
1. Register presets
2. Reading time and holds
3. Pace and density
4. Easing, springs, staggers
5. Staging and composition
6. Type and legibility
7. Colour and light
8. Camera
9. Transitions
10. Acting (characters)
11. Data, explainers, honesty in graphics
12. Engineering: determinism, capture, blur, encode
13. Multi-format and parallel builds

---

## 1. Register presets

| | Clean / premium | Handmade / playful | Editorial / documentary | Kinetic |
|---|---|---|---|---|
| fps | 60, with subframe blur | 24, animating on twos (12 drawings/s) while the camera stays smooth at 24 | 30 (or 24) | 30 or 60 |
| Spring ζ (damping ratio) | 0.72–1.0; camera and text 1.0 | 0.4–0.7; one elastic moment per film | 0.85–1.0 | 0.75–1.0; snaps land on the beat |
| Overshoot | ≤ ~5%, only on clicks, state flips and the hero | Squash and stretch allowed, to taste | Almost none | One hero punctuation per chapter |
| Texture | None: no grain, glow or particles | Grain (added in post), line boil, paper | Restrained grain allowed; never nameable | Flat, high contrast; ground colour rotates between shots |
| Motion blur | Subframe blur on fast moves only | Usually none (animating on twos) | Light | On slams and whips |
| Density | One thing moves at a time | Secondary action and idle life | Fewer moves, longer holds | A cut every 1–4 beats; holds on the reads |
| Typical length | 15–45 s | 30–90 s | 45–120 s | 15–60 s |

Mapping the brand onto two axes refines the preset:
- **Energy** (low ↔ high) sets duration, overshoot and squash.
- **Tone** (serious ↔ playful) sets how much paths curve and how much secondary action there is.

Self-check: three words describing the motion should match three words describing the brand.

## 2. Reading time and holds

Count holds from the moment the text has **finished arriving** until it starts to leave.

| Content | Minimum hold |
|---|---|
| On-screen text (Latin) | max(1.5 s, 1.0 s + 0.3 s × words) |
| On-screen text (CJK) | max(1.5 s, characters ÷ 4.5 + 1.5 s) |
| Title or chapter card | 2.5–4 s |
| Final message, wordmark | ≥ 2 s; brand or wordmark holds ≥ 1 s *completely still* |
| Subtitles | max(1.8 s, spoken duration + 0.6 s) when there's room; ≤ 3.5 words/s (≈ 17 chars/s); no gaps of 1–3 frames between cues. With continuous VO, chunk by phrase and let each cue run until the next one starts. Merge phrases that would come out shorter than 1.8 s rather than overlapping cues |
| Comparison before its verdict | Each item fully in frame ≥ 2.5 s |
| Any information-bearing element before a cut | ≥ 1 s still |

The sources' formulas ranged from about 1.5 to 3.5 s for a six-word line. The middle value is given here. When unsure, hold longer, because every source's pacing feedback went one way: slower.

The reads model sets the shot length:
- list each read in order;
- give each time to be found, understood and registered;
- don't start the next read while the last is still landing.

Small, distant, fast or subtle reads take longer.

Text that animates in counts as visible only once complete. A typewriter effect counts from its *final* character.

## 3. Pace and density

- **The two failures:**
  - **Slideshow:** a single stagger at t=0, then three dead seconds.
  - **Screensaver:** six elements on six endless loops.

  Aim for several cued events, each completing, then a still read.
- **New information every 2–4 s.** Never more than ~1 s fully dead outside a designed hold. "Living" holds come from one secondary element: light breathing, a 1–3% camera creep, an idle. Never use handheld shake for this, and never animate data or wordmark holds.
- **Acceleration:** halve the intervals (0.5 → 0.25 → 0.125 s), never shorter than 3 frames. A mass entrance accelerates hard, as in dealing cards, then gets ~0.5 s of stillness.
- **At least one breath:** a held pause or long take. In a 30–60 s film, aim for one before the turn.
- **Emphasis budget:** the lead section gets about 35–40% of the runtime. If one section balloons past half, add time to the others rather than cutting it *(single case)*.
- **Arc defaults:**
  - **Promo:** brand open 8–12% → single-hero showcase 12–15% → feature climb 55–65%, alternating high and low energy with a breathing card every 1–2 features → finale at peak energy 13–16%.
  - **Narrated launch:** problem 8–10% → agitate 8–10% → thesis 5% → product 30–35% → proof 20–25% → contrast 10% → call to action 8–10%.
- **Something new every shot.** A shot with no event reads as a bug, so a beat needs an event, not just motion.

## 4. Easing, springs, staggers

**Easing by role:**

| Role | Curve | Duration (1080 canvas) |
|---|---|---|
| Entrance (strong ease-out) | cubic-bezier(0.16, 1, 0.3, 1) | Small UI 0.25–0.4 s; word or line reveal 0.5–0.8 s |
| Exit (ease-in, leaves fast) | cubic-bezier(0.6, 0, 0.9, 0.35) | 40–60% of the entrance |
| Move between states | cubic-bezier(0.65, 0, 0.35, 1) | Large moves 0.6–1.1 s |
| Value that "lands" | cubic-bezier(0.55, 0, 0.2, 1.12), or a spring | |
| Continuous drift, rotation, grain | Linear | |

Entrances need opacity **plus** 10–28 px of travel (or 0.86–0.99 scale). Opacity alone looks like a fade-in template.

**Springs: closed form, summed.**

For a target change at time t₀ from a to b, use ω = 2π·f and τ = t − t₀:
- **Underdamped (ζ < 1):** x(τ) = b − (b − a)·e^(−ζωτ)·[cos(ω_d τ) + (ζω/ω_d)·sin(ω_d τ)], where ω_d = ω·√(1 − ζ²).
- **Critically damped (ζ = 1):** x(τ) = b − (b − a)·(1 + ωτ)·e^(−ωτ).

Rules for using them:
- A value with several targets is the **sum of one spring per change**, never a restarted ease. That keeps everything a pure function of t.
- Issue the target about one settle-time early (~0.3 s) when it has to *arrive* on a beat.
- Typical f: 1.5–3 Hz.
- Leading and trailing edges on different springs (for example ω 34 vs 19) make a shape stretch as it moves.

**Staggers:**
- Words 0.05–0.09 s.
- Row cells 0.03–0.04 s.
- List items 0.05–0.06 s, or 0.10–0.15 s if they should be *counted*.
- Check that offset × (n − 1) + duration ends before the next cue.

**Craft details:**
- **Anticipation:** compute it in pixels at delivery size. A 4 px wind-up is invisible; 30–50 px reads. Hand actions take 0.15–0.25 s.
- **Children lag parents** by 2–4 frames. Scale, rotation and shadow settle *after* position.
- **Avoid twinning:** code copies values exactly, so offset phases, seeds and amplitudes.
- **Velocity-driven secondary motion:** derive squash, trails and lean from v = x(t) − x(t − Δ). Don't run separate clocks.
- **Settles:** move by a per-frame law, never in 3-frame steps.
- **Hard limits that read wrong past the threshold** *(single case each)*:
  - a crash zoom over 10 frames reads as an ordinary push;
  - shake over ~20 px reads as a glitch;
  - a negative or flash frame of 4 frames or more is *seen* rather than felt.

## 5. Staging and composition

- **One focal point per frame.** Lead the eye to it before the read: it moves first, lights up, gets looked at, or the camera moves to it.
- **Subject size:**
  - at least ⅓ of frame height at key moments;
  - a UI subject fills 50–75% of frame width;
  - a character takes up about 40% of frame height in medium shots;
  - tiny subjects belong only in establishing wides.
- **Safe areas:**
  - **16:9:** ≥ 96 px margins.
  - **9:16:**
    - keep essentials inside x 60–1020 and y 250–1500, with nothing important in the bottom ~20% (platform UI);
    - decide the centre-square safe zone at storyboard time if the same timeline must also render 1:1.
- **Every pause is a poster.** Each hold should be a designed composition, and so should the final frame.
- **Depth:** separate foreground, mid and background. The hero gets a light, and the background is never a dead flat fill.
- **Captions belong to the world:** an inscription, a label, a HUD plate in the style's language. A generic lower-third bar doesn't.
- **Subtitles:**
  - never over the subject;
  - one line per language;
  - split a long line into two cues rather than wrapping it.

## 6. Type and legibility

- **Faces:** at most three families, by role: display, UI or body, and mono for labels. Set the brand font explicitly; the model's default font is a fingerprint.
- **Scale at 1080:** mega 260 / display 180 / h1 120 / h2 84 / h3 60 / body 40 / small 32 / label 24. Labels below 24 px are texture, not text.
- **Display type:** tracking −0.02em, line-height about 1. Pair contrasting weights (900 vs 400).
- **Numerals:** tabular numerals for anything that counts. Odometers need each slot sized to its final glyph.
- **Floors** (measured in *rendered* pixels, after scale, zoom and cos(rotY) foreshortening):
  - the primary message ≥ 56 px, about 5% of frame height;
  - secondary text ≥ 32 px;
  - nothing meant to be read below 24 px.
- **Accent words:** one per line, through italic, weight or the accent colour.
- **Mono labels** are decoration: uppercase, tracking 0.2em, muted.
- **Swaps:** text inside a morphing container gets its own enter and exit windows. The old text exits short and early, and the new text never overprints it. Outgoing titles leave before incoming ones occupy the same space.
- **Sharp text in 3D or under zoom:**
  - rasterize at 2–4× and scale down;
  - never put `will-change` on anything the camera scales;
  - never blur text that is meant to be read;
  - debug in this order: capture scale → raster path → scaling method → camera.

## 7. Colour and light

- **Colour logic, not a palette:**
  - one neutral ground;
  - one accent, with its meaning written down;
  - at most one tint;
  - the value order (what is lightest or darkest).

  The accent stays small and goes to the hero. A third hue is almost always a mistake.
- **Grounds:** a hue-tinted dark, never #000. No large areas of pure #fff.
- **Colour flips:** if a film flips its ground colour, every flip is a story turn.
- **Contrast:** text ≥ 4.5:1 against what is actually behind it. Measure with the grade off as well as on, because a full-frame grade fools contrast samplers.
- **The grade:** if a viewer can name the effect, it is too strong. Glows are driven by state, not time.
- **Light in paint styles:** additive, because mixing pigment turns yellow over blue into mud.
- **Morphs:** morph through a neutral, never blend two saturated wall colours.

## 8. Camera

- **Use one world→screen function** for everything that tracks a subject. Put a world point on a screen point; zooming about a point drops the subject under the caption.
- **Rig structure:** keep rotation and scale on separate nodes. Interpolate zoom in log space. Key the camera as [t, zoom, x, y] on one container.
- **Settle before the action:** the camera holds still through a click or reveal, because a moving camera steals the click. Put the zoom origin on the clicked control so it stays fixed.
- **Variety:** use several *different* motivated moves (about four in 30–60 s), plus one memorable signature shot.
  - Never repeat the same move on adjacent shots.
  - Never zoom in and straight back out.
  - 2D has a camera too: push, pull, parallax, focus pulls, frames within frames.
- **Angles:** legibility decides. Shoot information-dense shots straight on; text close-ups at a slight side angle; save stylized tilts for single shots.
- **Accents:**
  - beat punches of 1–3% scale that decay exponentially;
  - shake 3–18 px decaying as e^(−14·Δt), and never in product promos;
  - no camera drift at the end of data or hero shots.
- **Cut seams:** cut at peak velocity. Match direction and speed on both sides, and keep the sign of the zoom velocity. The next shot enters already moving in the direction of the exit.

## 9. Transitions

Pick one transition per seam at storyboard time, each with a reason you could say aloud.

| Link | Use when |
|---|---|
| Next step | The process continues |
| Match on position | Two subjects share a shape or place |
| Shape morph | One thing *becomes* another; costs ~1.2 s |
| Scale through | Zoom into the element the eye is on; it becomes the next scene |
| Iris | Open from whatever just lit up; ease by area, not radius |
| Cause → effect | An action on one side causes the other |
| Push + flash | A push with a white flash straddling the cut, ~5 frames on each side |
| Whip pan | A continuous velocity curve with a long braking tail |
| Time cut | Same frame, changed by time |
| Callback | Return to an earlier image, changed |

Budgets and rules:
- Transitions take 0.45–0.6 s, borrowed from the neighbouring shots.
- At most three morphs in a film under 30 s.
- Never stack a transition and a flash on one seam.
- Never use three *decorative* transitions of the same kind in a row (wipes, flashes, whips, irises). A continuity mode's native link (every seam a morph in a morph chain) doesn't count. Vary what each morph does instead: shape, scale, colour.
- Bridge objects are ≥ 200 px and in frame at the boundary.
- Never leave blank frames in a transition. Clamp local `t` so a scene is never drawn at negative time.

## 10. Acting (characters)

- **One drawing function** per character keeps it on-model. Emotions blend through keyframes; never switch a pose inside an `if`.
- **Anticipation → action → follow-through.** Show the thought: the eyes move first. A strong key pose reads as a still.
- **Exaggerate:** subtle reads as nothing at phone size. Check eyebrow direction at final size, because worried and angry are one flip apart.
- **Contacts:**
  - held props sit between the palms;
  - feet meet the ground;
  - a rolling object turns by distance ÷ radius.

  Check contacts with a crop that follows the world point through the camera.
- **Idles:** lock idles to the BPM, even without music; use half-time for ballads. Nothing stands smiling while nothing happens.
- **Cause, then reaction,** in sequence, with time for the reaction. Pay off every set-up.

## 11. Data, explainers, honesty in graphics

- **An animation is a graphic, not data.** Only end values and dated anchors are facts. A counter stops on the caption's value while the caption is up.
- **Context:** real axes, labels and units. A number without a unit is a defect.
- **Labels:** illustrative or schematic visuals say so on screen (`SCHEMATIC`, `ILLUSTRATION`, `Example data`) for as long as they are visible. Exaggerate only with an on-screen note, and measure on the undistorted data.
  - An honesty label isn't chrome. Put it *on or beside the graphic it qualifies*, in the film's caption style, at ≥ 24 px.
  - It never goes in a screen corner or a HUD strip.
- **Simulate the real thing:** a random walk is an actual random walk, and a proof's mechanism maps to its operations.
- **Mark interpretation as interpretation.**
- **Attribute single-source claims** on screen and in the voice.
- **Image resolution ceilings:**
  - photos ≥ 1 source px per screen px;
  - modern footage ≤ 1.5× upscale;
  - archive film ≤ 2.5×.

## 12. Engineering: determinism, capture, blur, encode

**The determinism contract:**
- No `Date.now()`, timers, CSS transitions or carried state.
- Seeded PRNG only (for example mulberry32 or a hash of `(seed, frame)`).
- Stateful simulations are precomputed into arrays at load; `render(t)` only reads them.
- Library time is set explicitly (GSAP `tl.totalTime(t)`, WAAPI `currentTime`, Lottie `goToAndStop`).
- Test: render frames in reverse order and diff them against a forward render. Any difference means hidden state.

**Page contract (HTML):**

```js
window.DUR = 24.0;            // seconds
window.FPS = 60;
window.READY = (async () => { await document.fonts.ready; /* decode images */ })();
window.seek = async (t) => { /* set every style/draw from t only */ };
window.TEXTS = (t) => [ /* {text, x, y, w, h} for readable text fully shown at t */ ];
window.CUES = timeline;       // exported from the single timeline, for QA and sound
```

**Capture loop** (Playwright or Puppeteer):
1. Load the page and await `READY`.
2. Kill all CSS transitions and animations.
3. For each output frame and each subframe:
   1. `await seek(t)`;
   2. wait two `requestAnimationFrame` callbacks;
   3. screenshot.
4. A JS page error or a 404 on a script stops the render rather than producing a broken film.
5. Render in chunks with parallel workers, and retry failed chunks.

**Motion blur:** render N subframes per output frame at t = frame/fps + ((i + 0.5)/N − 0.5) · shutter/fps, for i = 0…N−1. `shutter` is the fraction of the frame interval that is open: 0.5 is a 180° shutter, the natural film look, and 1.0 is 360°. Blend the subframes with ffmpeg `tmix=frames=N` and keep every Nth frame.
- **Choosing N adaptively:**
  - 1 when nothing moves;
  - 4 when the fastest element moves ≤ 20 px per frame;
  - otherwise about ⌈px ÷ 5⌉, capped at around 16–64.

  Four subframes ghost on fast whips, so use 8 there.
- **Restrict blur:**
  - never blur across a hard cut;
  - keep blur off text that is meant to be read;
  - reserve heavy blur for the 1–3 slam moves.

**Texture:**
- Add grain in ffmpeg (`noise` or an overlay) rather than in the page. Per-frame page grain makes every frame incompressible.
- If grain must live in the page, re-seed it at about 12 Hz, not every frame.

**Encode:**
- H.264, yuv420p, BT.709 tags, TV range.
- Master CRF 14–19, `-preset slow`. Use `-tune film` for texture and `-tune animation` for flat art.
- AAC 256k.
- Draft renders: half resolution, 30 fps, CRF 23–28. Use them to judge rhythm, not sharpness.

**Traps that recur:**
- An unseeded RNG inside `render(t)` makes parallel workers disagree.
- A NaN in geometry or in `pow()` of a negative number blacks out a frame, or silences a whole synthesized mix. Clamp inputs.
- Line weight scales with camera zoom. Keep hairlines constant in screen space, or draw close-ups at native scale in a call-out.
- Masked type can peek in at progress 0. Hide it explicitly.
- Strip canvases that are too short expose seams on a tilt.
- If a draw function hides an element, it has to un-hide it as well.

## 13. Multi-format and parallel builds

- **Several aspects from one timeline:** write scenes against a layout function and *reframe* each aspect. Never crop 16:9 into 9:16.
- **Parallel agents, one file per shot group:**
  - shared files are read-only;
  - each agent's brief contains the approved panels, the style spec, its time range and cue names, the bridge objects that must be in frame at its boundaries, and the determinism rules;
  - the orchestrator builds one reference section first, then renders and checks every seam itself.
