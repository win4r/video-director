# What makes LLM-coded video good: methodology extracted from eight repositories

This document extracts the method behind the better work across eight public repositories about videos an LLM writes as code. The code is HTML, Canvas, SVG, Three.js, GSAP or Remotion, rendered frame by frame to MP4. The aim was the principles that actually drive quality, not a catalogue of examples. The synthesized skill lives in [`video-director/`](video-director/SKILL.md).

## Sources and what each contributes

| Repo | What it is | Signature contribution |
|---|---|---|
| **yihui-dev/awesome-opus5-5-videos** | 703 shared prompts, 100 featured remakes | Which prompt levers recur in strong prompts, and what weak prompts leave out |
| **tuzhechen2005/opus-video-skills** | Two style skills (kinetic reel, painted animation) | The **"reads" model** of viewer timing; acting and animation principles; the emphasis budget |
| **whaleyxbt/claude-motion** | Remotion taste rules, a review loop, procedural sound | **Numbers as deliberate defaults**; one timeline.json for picture, sound and review; contact sheets per beat |
| **howseen-ai/claude-motion-design** | HTML `seek(t)` studio skill | "The prompt is 10%, the harness is 90%"; signal-level QA (pops, flashes, loop seams); default-reject critics |
| **AbubakrChan/product-launch-motion** | v1, voiceover-led and disciplined; v2, music-led single-shape grammar | **Slideshow vs screensaver**; reveals cued to something; truth whitelist; why the skill shrank from about 3,900 lines to about 120 |
| **lemomo-ai/lemo-opuscar** | A "director" system with about 61 style specs | **Benchmark first**; three structures to escape the cliché; style invariants kept apart from story; perception turned into pass/fail scripts |
| **Vincentwei1021/video-shotcraft** | Product-promo pipeline, 124 shot cards | **Rules as case law** (rule + precedent + self-check); beat-grid fitting; independent clean-context review; data from 216 redesigned shots |
| **cth9191/animate** | A grammar measured from 16 reference films, with plug-in styles | **Format grammar** (engine × stage × clock × medium, with coupling rules); story invariants; numeric arc checks |

**A caveat on evidence.** The prompt collection's "featured" flag mostly tracks early virality and the curator's taste. All 285 entries without a remake were added on one day, so "no remake" means "new", not "worse". Its statistics are suggestive, not causal. The stronger evidence is convergence: the same rule reached independently by several authors, each from their own failures.

---

## 1. The central finding

Quality comes from the harness: the process, the numbers and the checks wrapped around the model. Clever wording in the prompt matters far less. Two observations make the point:

- **Short prompts can still produce great films.** In the prompt collection, featured one-liners such as "make a dynamic 15-second motion graphics video… go all out" got strong results when they ran inside a harness (Remotion or HyperFrames) that supplied the craft. The long, engineered prompts are those same harnesses written out by hand.
- **Every skill repo ends up with the same workflow:**
  1. Decide the idea.
  2. Write the plan in numbers.
  3. Prove the look on stills.
  4. Build as a pure function of time.
  5. Design sound on the same clock.
  6. Measure the delivered file.
  7. Have someone other than the builder judge it.

The agent's main handicap is that it cannot watch or listen in real time. The best repos treat this as the central design problem. They turn perception into measurement: read-time checks, frame-difference scans, loudness meters, beat-grid residuals and contact sheets. Their honesty rules forbid claiming anything the agent has not measured or looked at.

---

## 2. Convergent principles (reached independently by four or more repos)

Each principle below gives the rule, why it works, and the repos that reached it independently.

**1. Time is the only input.**
- *Rule:* every frame is a pure function of `t` or the frame number. No timers, no CSS transitions, no `Date`, no unseeded randomness, no state carried between frames.
- *Why:* any frame can be rendered alone, in parallel or out of order, and re-rendered to verify a fix. Non-determinism shows up as flicker, drift and parallel workers that disagree.
- *Who:* all eight. animate tests it by rendering twice in reverse order and diffing (tile.mjs).

**2. Plan in numbers before writing code.**
- *Rule:* a single timeline (beat map, cue sheet, frame table) names every beat in seconds. Picture, score, SFX, subtitles and checks all read this one source.
- *Why:* sync holds by construction, a retime is a single edit, and the plan can be reviewed before it costs anything.
- *Who:* whaley (timeline.json), lemo (timeline.js), tuzhechen (cues.js), animate (TIMELINE), PLM (a cue table annotated by word), shotcraft (frame table with acceptance frames), howseen (BEATMAP.md), and the strongest prompts ("show the state list on the beat grid before code").

**3. Make the cheap artifact first.**
- *Rule:* text plan → stills (styleframes) → storyboard → low-res draft → master. Direction questions never reach the expensive per-shot phase.
- *Why:* rendering costs about 1–1.5 minutes per second of film. A wrong subject is the most expensive mistake there is (animate), and a rendered video is a poor format for proposing a style (shotcraft).
- *Who:* all eight.

**4. One idea, one hero.**
- *Rule:* one subject, one claim, one turn. One constant the eye can hold, one hero moment, one central formal idea.
- *Why:* two ideas means neither gets remembered (PLM). The hero moment is what the rest of the film builds toward, so spending it early wastes it (whaley).
- *Who:* PLM (one claim of ≤7 words, landing within 10 s), lemo (one subject, goal and turn), animate (one constant, one sayable device revealed at 80–95% of the runtime), whaley, shotcraft (a single hero in the opening), tuzhechen (one focal action), and the prompt collection ("one strong formal idea per scene").

**5. Every reveal is cued to something.**
- *Rule:* reveals land on a word, a beat, the end of a read, or an on-screen action.
- *Why:* a reveal cued to nothing is the slideshow failure. Its opposite, everything drifting on independent loops, is the screensaver. The target sits between them: several cued events, each of which completes, then a still read (PLM).
- *Who:* PLM, animate, lemo (cue map), shotcraft, tuzhechen, howseen.

**6. Time it for the viewer.**
- *Rule:* the information has to hold still long enough to be read. Make actions fast and meanings slow.
- *Why:* the author knows what happens and the viewer doesn't (tuzhechen). Across six rounds of feedback in shotcraft, the note was always "slow down" and never "too slow". PLM v2 resolves energy against readability by keeping the beat alive with secondary motion and sound, not by rushing the read.
- *Who:* all eight. Their numbers vary (see the tensions table below).

**7. Objects carry continuity.**
- *Rule:* persistent objects travel between scenes and change role. Every cut has a reason you could say out loud. The same camera move never appears on two adjacent shots.
- *Why:* it makes the piece feel designed rather than assembled (whaley). Carrying one customer across four shots did more than any effect (PLM).
- *Who:* all eight. Generic wipes and crossfades are banned almost everywhere.

**8. Colour has a job.**
- *Rule:* one accent, reserved for one meaning: the hero, the finding, "the AI". Never colour on the same colour. Use tokens only.
- *Why:* "If everything is coral, nothing is" (whaley). The one coloured thing becomes the protagonist (lemo, swiss-motion).
- *Who:* all eight.

**9. Sound is designed on the same clock.**
- *Rule:* accent events; don't narrate every motion. Put silence before the payoff and the loudest hit on it. Place each SFX by its measured peak, not by where its file starts.
- *Why:* sound is half of the perceived quality. Over-scoring sounds cheap: 29 whooshes in 84 s were "cool at first, then annoying" (tuzhechen).
- *Who:* lemo, animate, PLM, whaley, shotcraft, tuzhechen, howseen.

**10. Measure the file you deliver.**
- *Rule:* check loudness, sync and frames on the final MP4, not on the source or the WAV. Read the audio envelope, not a window peak.
- *Why:* PLM found an inaudible cue and a clipped master only by measuring the delivered file. Gates catch *broken*, not *bad*, so they come first and judgment comes after.
- *Who:* PLM, lemo, animate, whaley, howseen, shotcraft.

**11. Review stills, not playback.**
- *Rule:* make contact sheets at moments just inside each beat (+0.3 s), dense strips around fast moves and transitions, and a sheet at 360 px wide to check readability on a phone.
- *Why:* the agent can look at frames but cannot watch video. Captures at a beat boundary miss what happens inside it.
- *Who:* all eight.

**12. The builder doesn't judge its own work.**
- *Rule:* a clean-context critic that defaults to reject. It cites evidence by frame and sorts findings into must-fix, nice-to-have and unverifiable.
- *Why:* the author knows what each frame is supposed to say. A fresh agent that can restate the film's message from the frames alone is the real test (howseen).
- *Who:* shotcraft, howseen, PLM (review passes), and creators in the prompt collection who ran 3×3 agent rounds or a fresh critic with a ledger.

**13. Tell the truth on screen.**
- *Rule:*
  - every number comes from a facts file with a source;
  - illustrative content is labelled ("SCHEMATIC", "Example data");
  - the product's real UI is used, never invented;
  - words are no stronger than their source.
- *Why:* buyers spot fakes. A paraphrased quote under a real photo is a lie, and watching the film never catches it; only checking against the source does (PLM).
- *Who:* PLM, lemo, tuzhechen, animate, howseen, shotcraft, and prompts in the collection.

**14. Ban the default look.**
- *Rule:* explicitly ban the model's fingerprints:
  - a centred title on a gradient;
  - everything fading in;
  - corner labels, borders and HUD chrome;
  - glows, particles and lens flares;
  - bouncy easing; linear motion;
  - crossfades;
  - grey placeholder UI and tiny text;
  - the default font; crowded vertical stacks.
- *Why:* left unconstrained, these are what the model produces. Four authors in the collection banned corner chrome independently. Shotcraft's 879 redesign notes are mostly these same tells.
- *Who:* all eight.

**15. Escape the first idea.**
- *Rule:* write three candidate structures and kill two. Pick a benchmark reference and take its grammar, never its content. Write the treatment *before* opening any example.
- *Why:* the first idea for a style is usually its cliché (lemo). PLM's own evals found that "sameness survives in structure after it has been eliminated from surface".
- *Who:* lemo, PLM, shotcraft (≤3 directions), animate ("map its beats; don't reskin").

## 3. Single-lineage ideas worth keeping

- **The reads model** (tuzhechen):
  - list, in order, what the viewer must understand in each shot;
  - each read needs time to be *found*, *understood* and *registered*;
  - one read at a time;
  - the reads set the shot length.
  
  A demo ending that ran 1.3 s became seven sequential reads over about 4 s.
- **Benchmark before anything** (lemo). One or two reference works chosen for *this* topic, each with "what to learn" and "what not to take". The author ranks this above every other rule.
- **Format grammar with coupling rules** (animate). A piece is engine × stage × clock × medium:
  - spatial plots get a follow-camera and no cuts;
  - chronologies transition through the scene;
  - lists cut on the beat;
  - a voice takes over the clock.
  
  Format rules must not be generalised across formats.
- **Rules as case law** (shotcraft). Each rule has an actionable sentence, a precedent (the verbatim complaint and how it was reworked) and a self-check question. Parameters carry their epistemic status ("single-case precedent", "speculative"). A real user ruling outranks a preset.
- **Invariants vs instances** (lemo):
  - a style spec holds only the invariants;
  - a demo is one instance;
  - numbers measured in a demo get promoted into rules;
  - pitfalls are recorded as failure → fix pairs.
- **Perceptibility thresholds** (shotcraft). Compute the motion in pixels before choosing ratios. A 4 px anticipation was invisible and had to grow twelvefold.
- **Notes are symptom reports** (PLM). "Make it 3D" turned out to mean a camera rig plus a coordinate refactor. Translate each note into the mechanism behind it.
- **Emphasis budget** (tuzhechen). Viewers notice proportions. When a lead chapter took about 60% of the runtime, the fix was to add time to the others, not to cut it.
- **The busiest moment is not the loudest** (animate). Peak density comes just before the silence; the loud hit is the turn.
- **Decision log for autonomy** (PLM v2 and the collection). Don't ask permission for creative calls. Log each as a DECISION and list them at the end so any one can be overturned in a single reply.
- **Silent one-sentence test** (howseen). Someone watching muted should be able to sum up the film in one sentence. If they hesitate, too much is moving.
- **Beat grids are fitted, not trusted** (shotcraft, howseen, animate):
  - fit t = t0 + i·T to the onsets by least squares;
  - test half and double tempo against transient coverage;
  - require a residual of about ±15 ms or better;
  - re-fit on the rendered audio.
  
  A tempo scalar was 2% off; an automatic grid was two beats off.

## 4. Tensions, and how the skill resolves them

The repos disagree, usually because they target different genres. The skill turns each disagreement into a **dial** chosen per film, with coupling rules. It does not pick one house style.

| Tension | Sides | Resolution in the skill |
|---|---|---|
| Density | "Hold longer, animate less" (whaley) vs "something new every 2–4 s, nothing still > 1 s" (howseen, shotcraft, animate) | The subject holds still while it is being read. At most one secondary element keeps life (light, idle, a slow creep). *New information* every 2–4 s, not new motion |
| Continuity | One shape, never cut (PLM v2, howseen, twoclipping prompts) vs cut on the beat (animate beat-cut formats, KR chapters, whaley's director) vs a transition at every seam (PA) | **Continuity-mode dial**, coupled to the plot engine |
| Clock | Lock to spoken words (PLM v1) vs beat grid (PLM v2, shotcraft, howseen) vs reads (PA) | **Clock dial.** A voice outranks the music when both are present; the reads set the minimum in every case |
| Spring feel | ζ ≥ 0.72, premium (howseen prose) vs ζ ≈ 0.4–0.55 pops (whaley, howseen code) | **Register dial**, with ranges per register |
| Texture | Grain, line boil and vignette (whaley, lemo, PLM v1) vs clean, with glows and particles banned (PLM v2, howseen) | Register dial. Even where texture is allowed, the viewer must not be able to name the grade |
| Text | Type as the hero (KR) vs captions in the world (animate, lemo) vs no text at all (PA) | **Text-policy dial.** Invariant: anything meant to be read is legible and held |
| Sound source | Synthesized (whaley, PLM v2, tuzhechen) vs samples placed by peak (howseen, shotcraft) | Either. Invariant: placement by measured peak, and the final mix is measured |
| Truth | A strict figures whitelist (PLM v1) vs invent the micro-story and disclose it (PLM v2) | Headline numbers are true and sourced; illustrative material is labelled; disclose in the report |
| User gates | Five gates (shotcraft co-creation) vs one question round (lemo) vs autonomy plus DECISIONs (PLM v2) | **Interaction mode** chosen up front, with at most one question round |
| Frame rate | 24 (lemo, animate) vs 30 (KR, PLM v1) vs 60 (PLM v2, whaley, howseen) | By register: handmade 24 on twos; data and narrated 30; UI and motion 60 with subframe blur |

## 5. What the prompt collection adds

**Most and least common features** (featured full prompts vs the newest batch without remakes):

| Feature | Featured | Newest, no remake |
|---|---|---|
| States a duration | 45% | 31% |
| Names a quality or reference anchor | 39% | 24% |
| Prescribes a technology | 13% | 36% |

Under 20% of either group specify palette, easing or verification.

**Three recurring skeletons in the strongest prompts:**
1. **Tagged template** (twoclipping lineage, copied at least 15 times): `<inputs>` with defaults, then `<direction>` with a Banned list, `<structure>` on a beat grid, `<build>` as a numbered technical contract, `<gotchas>`, and `<start>`, which acts as a gate.
2. **Film spec** (gdgtify):
   - central experience;
   - deliverable;
   - art direction;
   - LOCKED COPY;
   - CENTRAL VISUAL RULE;
   - timestamped storyboard;
   - choreography;
   - implementation;
   - QUALITY GATE at listed timestamps.
3. **Creative-director brief:**
   - role and stakes;
   - source of truth;
   - brand tokens;
   - rules with NOT lists;
   - emotional arc;
   - a suggested (not rigid) storyboard;
   - good and bad transitions;
   - guardrails;
   - a mandatory review loop.

**The levers they share:**
- numbers instead of adjectives (hex codes, seconds, damping ratios, pixels);
- time-pure rendering;
- offline capture with subframe motion blur;
- music as the master clock, *except* when there is speech;
- objects carrying the transitions;
- a banned list aimed at the model's defaults;
- stills before the full render;
- readability rules;
- truth guardrails;
- loop closure;
- an explicit interaction protocol: a plan gate *or* declared autonomy.

**Common failures:**
- stacked adjectives ("think big");
- kitchen-sink effect lists;
- missing duration, aspect, fps, deliverable form or verification;
- "glorified PowerPoint" results;
- stopping at a plan.

**Process reality.** "One prompt" claims usually hide iteration: one creator needed 90 messages and 33 takes, others went through two to four rounds of notes or multi-agent critique loops. Effort tiering helps: plan and judge at high effort, build at medium.

## 6. A meta-lesson about writing the skill itself

PLM v1 grew to about 3,900 lines of rules, references and examples. Its own evals found that the worked examples were *inherited*: films looked different on the surface and were built on the same chassis underneath. v2 cut back to a short skill, a strong small grammar and the user's verbatim prompts as the spec. The README notes that smaller models "follow the rules but miss the detail". lemo reached the same conclusion from another direction, with an anti-anchoring design and a check that the result is "not the demo again".

So the synthesized skill is deliberately **lean and schema-first**:
- principles carry their reasons;
- numbers are labelled as defaults per register;
- there is no shot library or style library to copy from;
- templates contain fields, not instances.

## 7. Deliberately left out

- **Organisation-specific plumbing:** personal paths, API keys, asset IDs, publishing integrations.
- **Two risky practices found in one repo:** cropping AI-generated faces to remove watermarks, and downloading memes with yt_dlp.
- **Catalogues:** shot cards, style specs and demo stories. The repos' own authors found they cause sameness. Their *schemas* are kept; their contents are not.
- **Engine-specific traps** that vanish under a pure `seek(t)` model, such as GSAP's `immediateRender` and HyperFrames' marker injection.
