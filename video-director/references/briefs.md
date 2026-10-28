# Briefs and templates

These templates are **fields, not examples**. Fill them from the user's topic. Don't borrow a story, an arc or timings from any previous film, since inherited structure is the most common way films end up looking alike.

## Contents
1. TREATMENT.md
2. timeline.json
3. FACTS.md
4. Shot spec (for complex shots)
5. Style spec (when a look should be reusable)
6. Prompt for another agent (full and minimal)
7. Parallel build brief
8. Delivery report
9. Fix card (revisions)

---

## 1. TREATMENT.md

```markdown
# <working title>

**Idea (one sentence):** <subject> <does/becomes> <turn>, so the viewer <understands/feels> <payoff>.
**Promise (≤ 7 words, on screen by 3 s):** <a tagline is not a factual claim; numbers, comparisons and "first/best/only" are, and go in FACTS.md>
**Hook (0–3 s, sound off):** <hook copy> at <px> · CTA: <install command / URL / none> at <px> · the hero later proves this; it doesn't withhold it
**Terms (said and shown):** <1–3 words this audience searches for: the subject's name, the standard term for each key property>
**Audience · channel · how it's watched:** <who> · <where> · <muted autoplay? phone?>
**Spec:** <W×H>, <fps>, <N s> = <frames> frames · deliverables: <mp4, poster, srt, no-music version, other aspects>

## Benchmark
- <work 1>: learn <composition/pacing/camera/colour/score shape> · don't take <characters/shots/melody/logo/font>
- <work 2>: …

## Structures considered
1. <shape, e.g. single journey / before→after / countdown / list that turns / document asks, footage answers>
2. <…>
3. <…>
**Chosen:** <n> because <reason tied to topic>. Rejected: <the other two, one line each>.

## Dials
Clock: <music grid @ BPM | voice | reads> · Continuity: <one-shape | morph chain | cut-on-beat | chaptered>
Register: <clean | handmade | editorial | kinetic> · Text policy: <hero | in-world | none>
Constant the eye holds: <…> · Accent = <hex> means <one thing> · Type roles: <display / UI / mono>

## Arc
Hook (0–3 s): <…> · Turn at <t>: <…> · Hero moment = payoff at <t>: <…> (the one native move)
Arc quantity: <what visibly changes> = <its value per beat> (loops: the invariant that holds)
Ending answers the opening by <rhyme | reveal of scale | done right the second time | bookend | other>
Actions that must be seen: <each one; a label never stands in for it>
Cast (if any): <LABEL> · silhouette · anchors in order · how it moves · screen side
Missing inputs and how they were handled: <no track → designed grid | no UI → promise acted in the user's world | VO ESTIMATED | …>

## Beat sheet
| # | t start–end | What happens | Reads (in order) | Cued to | Camera | Transition out (+ reason) | Sound | Guard (do not …) |
|---|---|---|---|---|---|---|---|---|

## Sound plan
Source: <user track | synthesized | silence> · Silences at <t> · Loudest hit at <t> (payoff) · Score growth: <…>
SFX vocabulary: <3–5 sounds and their material> · Voice: <none | script + voice character>

## Truth
On-screen numbers: see FACTS.md · Illustrative elements and their labels: <…> · Not claimed: <…>

## Risks / least-sure-about
<what you're least confident in; this is what to show the user if there's a gate>

## DECISIONS (autonomous mode)
- DECISION: <choice> because <reason>
```

## 2. timeline.json

This file is the one source of truth. Picture, SFX, score, captions and QA all read it. Times are in seconds as floats; round to frames only when rendering.

```json
{
  "meta": { "w": 1920, "h": 1080, "fps": 60, "dur": 0.0,
            "clock": "music|voice|reads", "register": "clean|handmade|editorial|kinetic",
            "loop": false, "bpm": null, "meter": "4/4", "bars": null, "t0": null, "songOffset": null,
            "grid": "fitted|designed|none", "hookWaiver": null,
            "vo": { "status": "RENDERED|ESTIMATED", "file": null, "rateWps": null } },
  "objects": [ { "id": "string", "role": "constant|hero|bridge|prop", "what": "string" } ],
  "vo": [ { "id": "L1", "text": "string", "from": 0.0, "to": 0.0,
            "words": [ { "w": "string", "t": 0.0 } ] } ],
  "scenes": [
    { "id": "string", "start": 0.0, "end": 0.0,
      "beats": { "name": 0.0 },
      "cueRef": { "name": "L3.word | bar5 | read:2" },
      "reads": [ { "what": "string", "from": 0.0, "to": 0.0 } ],
      "transitionOut": { "type": "string", "dur": 0.0, "why": "string", "bridge": "objects[].id" } }
  ],
  "reads": [ { "what": "string", "from": 0.0, "to": 0.0 } ],
  "cuts":  [ 0.0 ],
  "hero":  { "t": 0.0, "what": "string" },
  "silences": [ { "from": 0.0, "to": 0.0 } ],
  "sfx":   [ { "at": "scene.beat", "offset": 0.0, "src": "string", "gain": 0.0, "why": "string" } ],
  "captions": [ { "from": 0.0, "to": 0.0, "text": "string", "src": "vo:L1 | beat" } ],
  "texts": [ { "id": "string", "text": "string", "from": 0.0, "to": 0.0,
               "role": "hook|cta|term|null", "px": 0, "box": [0, 0, 0, 0] } ],
  "terms": [ "string" ],
  "camera": [ { "t": 0.0, "zoom": 1.0, "x": 0.0, "y": 0.0, "why": "string" } ]
}
```

Only `meta` (w, h, fps, dur, clock) and `scenes` are required; everything else is optional, and extra fields are fine. `scripts/check_timeline.py` validates it.

Rules:
- Components reference beats by name (`TL.scenes.hook.beats.slam`). They never contain bare frame numbers.
- Beats are numbers. If a beat derives from something else (a word, a bar, a read), record the source in `cueRef` and regenerate the number from it, so a retime is a single edit.
- **SFX and captions are always anchored to something.**
  - SFX are relative to a beat.
  - Captions derive from VO lines or beats.
  - Neither uses absolute times typed by hand.
- **Texts:** `from`/`to` (or `in`/`out` naming beats) bound the time the text is fully legible, and `check_timeline.py` holds each one to the read-time formula.
  - Mark the hook, the CTA and on-screen terms with `role`, and give their rendered font size in `px`.
  - Once the layout exists, add `box`: [x, y, w, h] in delivery pixels at `from`, the text's own bounds rather than its container. `qa_video.py` measures size and contrast there.
- **Terms** lists the words the film must say (if narrated) and show (SKILL.md principle 13).
- **Reads:**
  - Scene `reads` belong to that scene.
  - The top-level `reads` holds reads that cross scene boundaries, which happens in journey and one-shape films with no cuts.
- **Clocks:**
  - Music: beat times come from `t0 + n·(60/bpm)`. A `loop` must be a whole number of bars.
  - Voice: beat times come from the word timestamps in `vo`. While `meta.vo.status` is `ESTIMATED`, everything downstream is provisional.
- `qa_video.py --beats` reads `cuts`, `silences`, `hero`, `texts` (with a role), `meta.loop` and `meta.clock`.

## 3. FACTS.md

```markdown
| # | Claim as shown (screen / voice) | Source (URL or file) | Quoted wording | Date |
|---|---|---|---|---|

## Measured values
| Value | Method | File |

## Illustrative (labelled on screen as …)
- <element>: why it's illustrative, label used

## Not claimed
- <things the film deliberately does not assert>
```

If there is no FACTS.md, no numbers go on screen. Words can't be stronger than their source ("request for information" isn't "investigation"). Name the reference for every comparative claim ("from which peak?").

## 4. Shot spec (for complex shots)

Write one when a shot has several layers, a tuned move, or is being handed to another agent.

```markdown
### <shot name>: <one concrete visual sentence>
- **Function:** <narrative job: hook / showcase / proof / breather / payoff / outro> · **Energy:** low|mid|high|peak
- **Intent:** <what the viewer should understand or feel, and the metaphor that carries it>
- **Reads:** <ordered list with times>
- **Timetable:** anticipation <t> → action <t> → follow-through <t> → hold <t> (landmark frames)
- **Motion core:** <layer-by-layer build, with values>
- **Parameters:**
  | Parameter | Value | Too low reads as… | Too high reads as… |
- **Camera:** <move + reason> · **Transition in/out:** <type + bridge object>
- **Sound:** <cue per named beat>
- **Known pitfalls:** <failure → fix pairs; params that must not be "simplified">
- **Acceptance frames:** <2–3 frame numbers and what each must show>
```

The parameter table records *the feel at both failure edges*. That is what makes tuning transferable, so keep it even when a number changes.

## 5. Style spec (when a look should be reusable)

A style spec holds **invariants only**: no story, arc, beats, durations or end card. When a number measured in one film proves out, promote it to a rule here.

```markdown
# <style name>: <one-sentence essence of the medium>
References (grammar only): <work: what to learn> … never copy characters, shots, melodies, logos, fonts.

1. Essence & what it is not: 3–5 traits readable at a glance; confusable styles and the line between them
2. Materials & rendering: how code imitates the medium (layers, blend, noise, stroke), with parameters
3. Colour logic: rules, not a palette (hue count, ground, what the accent is reserved for, what never gets colour)
4. Type & captions: faces by role, sizes, how text belongs to this world, reading-time rule
5. Motion quality: fps/stepping, easing families, entrances/exits, what never moves
6. Camera grammar: move → what it expresses (a vocabulary, not a route; no row assigned to opening/climax/ending)
7. Sound palette: instruments, foley by material, ambience, silence, mix character (no BPM, key or arc)
8. Native moves: name · what it does · how to build · fits content like <3 examples unlike any demo>
9. Pitfalls: failure → fix pairs specific to the medium
10. Variation space: what each film decides; 3 structures, 3 openings, 3 endings far from any demo
Proven on: <films> · Not matched: <deliberate deviations from references and why>
```

## 6. Prompt for another agent

**Full brief.** Use this when the user wants a prompt to hand to an agent, or as the expanded form of a one-liner.

```xml
<inputs>
Ask me for: <copy/claim>, <assets: logo, screenshots, URL/repo>, <track or "score it">, <palette/fonts>.
If I skip any, use these defaults: <…>. Ask once; then decide and log DECISIONs.
</inputs>

<direction>
Purpose: <what it's for, where it plays>. Idea: <one sentence>.
Benchmark: <named work>: learn <…>; don't take <…>.
Format: <W×H>, <fps>, <N s>, <loop?>. Dials: clock <…>, continuity <…>, register <…>, text <…>.
Look: ground <hex>, ink <hex>, ONE accent <hex> = <meaning>, type <display/UI/mono>.
Motion law: <e.g. springs ζ 0.8, 0.6 s moves on cubic-bezier(.65,0,.35,1); exits half of entrances>.
Banned: <8–12 specific defaults to avoid>, and anything that looks like a template.
</direction>

<structure>
<BPM/bars or VO>. Hero moment at <t>: <…>.
| t | what happens | read | cued to | transition out | sound | guard |
</structure>

<truth>
Locked copy: "<exact words, exact order>". Facts only from <source>; label illustrative parts "<label>".
Real UI only (capture it); no invented features, quotes, or endorsements.
</truth>

<build>
1. One self-contained <engine> project; every frame a pure function of t (no timers, transitions, Date, unseeded random).
2. One timeline file drives picture, sound, captions.
3. <signature technique and how to build it>.
4. Capture offline at <fps> with <N> subframes blended (tmix); BT.709 H.264; −14 LUFS / −1 dBTP.
5. SFX placed by measured peak on the timeline's cues.
</build>

<gotchas>
<3–5 engine or style pitfalls known for this kind of film>
</gotchas>

<checks>
Before the full render: stills at <t1, t2, …> (+0.3 s after each beat) and a 360 px sheet; fix the 3 worst problems.
After: pop/flash scan, frozen stretches, cuts vs plan, loudness, loop seam. A strip for each action that must be seen.
Independent critic restates the idea from frames. Report every divergence from this brief and anything unverified.
</checks>

<start>
<"Show me the treatment and beat map before writing code." | "I'm away: decide everything, log DECISIONs, deliver the MP4.">
</start>
```

**Minimal prompt.** This is enough when the receiving agent has this skill:

```
Make a <N>-second <aspect> video for <audience/channel> that says: "<one sentence>".
Assets: <paths/URLs>. Facts: <source>. Music: <track | score it | none>.
Feel like <benchmark>, not <anti-reference>. <Ask first | Don't ask; log decisions>.
```

**Writing guidance for either form:**
- **Numbers over adjectives:** "0.6 s ease-out, 64 px", not "smooth, big".
- **A named reference over vibes:** "Linear launch film", not "premium modern".
- **Fewer asks than bans.** A list of a dozen effects turns into a kitchen sink.
- **Guards beside their beats.** A "do not" goes where the shortcut would happen ("do not simply fade in a finished caterpillar").
- **Name the right object.** Where a noun is confusable, name it and, once, the wrong one ("a chrysalis, not a silk cocoon").
- **Rank the priorities.** Mark the one sequence that matters most ("prioritize its drawing, staging and motion"), so trade-offs fall the right way.
- **Pick one interaction mode:** a plan gate *or* declared autonomy. Leaving it unstated produces either a stall or a surprise.
- **Treat any example storyboard as a starting point, not a template.** Say so in the prompt.

## 7. Parallel build brief

```markdown
You build shots <ids>, t = <start>–<end>, in <file>. Edit only that file. Shared files are read-only.
Read: STYLE/TREATMENT, timeline (your cue names: <…>), the approved panels for your shots.
Boundaries: <bridge object> must be in frame at <t> on both sides; enter already moving <direction>.
Rules: pure function of t; seeded RNG; no new globals; reference beats by name.
Verify: stills at your acceptance frames + strips across your seams; report a table:
| shot | frames | matches/close/rough | residual issue | what you could not verify |
Never claim a match you haven't viewed.
```

## 8. Delivery report

```markdown
**<title>**: <path to mp4> (<W×H>, <fps>, <dur> s) · also: <poster, srt, alt versions, source + one-command build>
**What it is:** <one sentence> · **Concept:** <benchmark + chosen structure>
**Scenes:** <t: one line each>
**Checks:** hook <copy> legible at <t> s, <px> px, <n>:1 · terms said/shown <n/n> · loudness <I> LUFS / <TP> dBTP · cuts vs plan max <n> f · pops <n> (explained: …) · frozen holds <list> · read-time pass <n/n> · critic scores <…>
**DECISIONs:** <list: overturn any in one reply>
**Real vs illustrative:** <…> · **Permissions needed:** <logos, likenesses, music>
**Actions shown:** <each action the brief names → the strip or time that shows it> · **Divergences from the brief:** <each, with the reason, or "none">
**Weakest shot:** <id + why> · **Not verified:** <e.g. audio measured, not heard; 9:16 version not reviewed>
**Would fix next:** <one line>
```

## 9. Fix card (revisions)

Write one card per failure. Several failures get one take each, structure and motion before surface detail.

```
DIAGNOSIS    <the failure→fix row (quality.md §5) and its likely mechanism>
SCOPE        <timecodes · shot · element>
KEEP         <style, composition, camera, timing, design: everything that must not change>
FAILURE NOW  <how it looks today>
TARGET       <named, observable features>
SHORTCUTS    <ways to fake it that are forbidden: enlarging, moving the camera, oversharpening, a change of style, added glow>
PROOF        <frames inside the scope to look at · frames outside it, diffed before encoding: identical>
```

As a prompt for another agent: "Change only <SCOPE>. Keep <KEEP> unchanged, but <change> so that <TARGET>. Avoid <FAILURE NOW>. Keep it stable in motion: no flicker, distortion or popping. Don't get there by <SHORTCUTS>. Everything else stays unchanged." Several cards become gated fixes: make fix 1, show its proof, then start fix 2.
