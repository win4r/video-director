# Sound: clock, grid, cues, silence, mix

Sound is half of what people perceive as quality, and it is the half you can't experience directly. Design it on the same timeline as the picture, measure everything, and tell the user that it was *measured*, not heard.

## Contents
1. Choose the clock
2. Music-led: picking the track and fitting the grid
3. Voice-led: script, VO, word timing
4. SFX: vocabulary and placement
5. Silence and the payoff
6. Mix and loudness
7. Verification

---

## 1. Choose the clock

| Clock | Use for | Coupling |
|---|---|---|
| **Music grid** | Promos, reels, loops, kinetic type | Structural changes land on bars, cuts on beats (or 2 or 4 beats), the drop on the hero moment |
| **Voice** | Explainers, narrated launches | Reveals cue to measured *words*; music is a bed ducked under the voice; don't force speech onto a dance beat |
| **Reads** | Silent stories, character pieces | Shot length comes from the reads; idles still lock to a nominal BPM so the motion has a pulse |

Rules that apply whichever clock you choose:
- **Voice takes over** whenever there is narration.
- **The song decides the arc** whenever the user supplies a track.
- **Cut on the grid only in beat-cut formats.** Morph chains and follow-camera journeys follow their own structure, not the grid.

## 2. Music-led: picking the track and fitting the grid

**Picking the track:**
- **Structure:** the track needs a build, a drop and an ending. BPM alone says nothing about energy.
- **Rough BPM-to-mood mapping** *(single source)*:

  | BPM | Feel |
  |---|---|
  | 60–80 | regal |
  | 90–110 | smooth |
  | 115–123 | sophisticated |
  | 125+ | hype |

- **Audition candidates inside the cut**, not on their own. The test is "sounds like a launch film", not "pleasant".
- **Licensing:** only a licensed track, or one the user provides.

**Fitting the grid.** Don't trust a tempo scalar or an automatic grid without checking it. Sources found them 2% off and two beats off.
1. **Build an onset envelope.** Use spectral flux, or the kick band (40–160 Hz) for the downbeat grid. For a busy mix, separate the drums first (HPSS or a stem splitter).
2. **Estimate the tempo** by autocorrelating the envelope, with a prior over 60–180 BPM that leans toward ~120.
3. **Fit by least squares.** Pick the onset nearest each predicted beat, then fit tᵢ = t₀ + i·T to all of them.
4. **Test half, double and ⅔ tempo** by how well each covers the transients. If kicks land on half-beats, the grid is twice too fast.
5. **Accept the grid only if all of these hold:**
   - at least 98% of beats matched;
   - mean error under 10 ms;
   - drift under 5 ms across the track;
   - beat 0 sitting on a real attack.

   Decide by these metrics, not by ear, since you have none.
6. **Find the drop** with band energy in 20–50 ms windows. Offset the song so the drop lands on the hero moment: `song_start = drop_in_song − drop_in_film`. Start the clip on a bar line.
7. **Classify hits by band.** The list of hits is a *candidate pool*, not a trigger list.

   | Band | Drives |
   |---|---|
   | Kick, 40–160 Hz | Impacts and slams |
   | Snare, 150–500 Hz + 1–3 kHz | Swaps and cuts |
   | Hats, 6–14 kHz | Density of micro-motion |

8. **Map the structure.** A table of RMS per section shows where energy is full and where the breakdowns are. A breakdown is a natural slot for a brand pause. Save the 2–3 strongest hits for the big moments.
9. **Keep times as floats in seconds** and round to frames only at the last step. Express beats as `beatT(n) = t0 + offset + n·T`.

**Frame-exact grids.** For cuts to land on whole frames:
- at 24 fps, 120 BPM gives 8th notes of 6 frames and 16ths of 3 frames;
- at 30 fps, use 112.5 BPM.

Otherwise accept a rounding error of up to half a frame and note it.

**Snaps** can start one note value early so they *land* on the beat.

## 3. Voice-led: script, VO, word timing

- **Write for the ear.** Short clauses, one claim, ≤ 3.5 words/s. Faster through the clauses, slower at the ends.
- **Render the VO before animating.** Frame length = measured VO + padding (0.2–0.5 s, longer before a hero beat). Never type durations by hand.
- **Get word timings** from ASR (Whisper or faster-whisper) or from the TTS engine's timestamps. Cue tables reference **words** ("`launch`@12.84"), because words survive a re-cut and bare seconds don't.
- **Cue the meaning, not the noun.**
  - Lead the travel so the hit lands on the word.
  - A beat carries at most two cues.
  - Start each visual beat ~0.3 s after the sentence ends.
  - About 200 ms of misalignment already reads as lag.
- **TTS hygiene:**
  - spell numbers out in the TTS text and show digits on screen;
  - compress or limit TTS before balancing (peak-to-RMS can be ~17 dB);
  - ASR-check every line, padded with ~0.6 s of silence. English should match word for word; CJK should reach a character similarity of 0.92 or more.
- **Put the payoff hit in the pause before** the line that names it.

## 4. SFX: vocabulary and placement

- **Accent; don't narrate.**
  - One action, one sound. Continuous motion stays silent.
  - About half the cuts get no sound.
  - Never use the same cue twice in a row.
- **Use a film vocabulary, not a UI-event one:**
  - whoosh for a camera move;
  - impact for a landing;
  - riser for a build;
  - sparkle for light;
  - real foley (paper, glass, switches, shutters) to match the material on screen.

  Avoid game-pack bleeps and notification tones. Generic noise whooshes wear out fast: 29 in 84 s went from "cool" to "annoying".
- **Budget:** one riser and one main impact per short film. Longer films can carry about 5 structural impacts, plus a sub-bass hit only under the hero reveal and the call to action.
- **Closing phrase** *(single case)*: riser → impact ~35 frames later (the loudest moment) → sparkle ~25 frames after that.
- **Repeated hits:**
  - alternate between two *different* samples;
  - step the volume down (for example 0.40 → 0.25 over 6 hits);
  - tighten the gaps;
  - when hits blur together, merge them into one swoosh.
- **Place by peak:** `start = cue_time − peak_offset_within_file − measured_output_offset`. The peak is the argmax of |s| or of the 10 ms RMS. Never align by the start of the file.
- **Tonal SFX** stay in the score's key (the pentatonic is safe), and their pitch can rise with progress and resolve on the payoff.
- **Pan** follows the on-screen x position, gently (±0.3).
- **Synthesized vs sampled:** either works. Synthesized sound is deterministic and in key; samples are richer. The fixed rules are placement by measured peak and measurement of the final mix.
- **Declare cues in a table:** `{beat or name + offset, src, gain}`, one comment per cue, all derived from the timeline. A change to the picture's timing then retimes every cue automatically.

## 5. Silence and the payoff

- **Silence is a tool.** Use at least one real silence before the turn or payoff, and two in a 30–60 s film. Make the drop 15–35 dB for 0.4–4 s while the picture holds, then end it with a hard stop: no reverb tail filling it.
- **The working definition** (shared with `qa_video.py`): a silence is ≥ 0.4 s in which the 100 ms RMS stays at least 15 dB below the film's 90th-percentile level *and* below −30 dBFS. A quiet bed under a loud film isn't a silence; the viewer has to hear the floor drop away.
- **Make the first sound after a silence one of the film's most important.**
- **Put the loudest moment on the payoff,** not on the busiest section. Peak density belongs just *before* the silence. With a voice clock, the voice is usually the loudest thing in the film. There the rule means the payoff hit is the loudest *non-voice* sound, placed in a pause in the VO and peaking at about the level of the voice.
- **Payoff recipe:** a ~0.4 s stab plus a sub, then a flat chord, with nothing busy on top.
- **Sound transitions:** use J-cuts and L-cuts, where the sound of the next scene arrives early or the last scene's sound lingers. Aim for at least two in a 30–60 s film.

## 6. Mix and loudness

| Layer | Level (relative) |
|---|---|
| Hero SFX | 0.25–0.35 gain on peak-normalized samples |
| Supporting SFX | 0.08–0.2 |
| Music bed under voice | ducked 4–10 dB (premium/editorial ~9–10; warm/handmade ~4–6) |
| Voice | ~10 dB above the music by RMS |

- **Level the asset, not the cue.** A volume multiplier can't rescue a quiet source. Normalize the file, or replace it.
- **Keep the low end in check:** hold 20–120 Hz about 3 dB below the rest, and keep pads out of the sub range.
- **Fade the first ~25 ms** of any hit that starts at sample 0. A hit at the very first sample overshoots in the AAC encode.
- **Master to −14 LUFS integrated, true peak ≤ −1 dBTP:**
  - use two-pass `loudnorm`, since one pass misses by about 0.5 LU;
  - aim a little lower (−1.5 to −2 dBTP) before the AAC encode, because encoding raises peaks;
  - after mastering, verify with `ebur128`. On short, dynamic films, loudnorm's own "Input Integrated" figure can disagree badly with a gated BS.1770 meter. On a 9 s test clip it read −7.0 LUFS where ebur128 read −14.0; the two agreed on steady tones.
- **A sparse mix can't reach −14 LUFS without crushing it.** Add a sustained bed, or accept a lower level and say so. Don't drive a limiter into it.
- **For seamless loops,** a static gain with no limiter keeps the seam clean (it lands around −15 LUFS).
- **Silent version:** deliver a no-music render from the same timeline when the platform or the user might want one.

## 7. Verification

- **Measure the delivered MP4,** not the WAV. Check integrated loudness, true peak, where the loudest 100 ms falls, and where the silences are (all reported by `scripts/qa_video.py`).
- **Read the envelope.** Check a cue's 100 ms envelope, not a peak over a whole window. A window peak once passed a cue whose first 56% was silent.
- **Draw a waveform with a line at every beat.** A hit falling between lines means a hard-coded time or a stale render.
- **Re-fit after rendering:**
  1. Extract the rendered audio and fit the beat grid again.
  2. Compare it with the picture's cut times.
     - ≤ 1.5 frames: ideal.
     - ≤ 3 frames: pass.
     - more than 3 frames: fix.
  3. If every offset is the same size in the same direction, it is encoder delay (AAC priming, ~1.3 frames at 48 kHz in one pipeline). Fix it with one constant; never edit the grid.

  Report the error in the audio itself separately from the error caused by quantizing to frames.
- **Account for what you can't hear.** "You can't hear the score": check per-section RMS, a spectrogram (`showspectrumpic`), and a count of any calls you meant to remove. Tell the user what was measured and what wasn't.
