// "Undertow" and the real-piano renderer, as they ran in index.html's sfx before the site switched to a Pixabay track.
// Not loaded by the site. It needs the Salamander piano samples in assets/piano/ (CC BY 3.0) and lived inside sfx
// (it uses its ctx and clamp).

  // "Undertow": slow, mysterious, cool solo piano in D minor, written note by note (in the spirit of Dolphin's
  // short piano pieces; nothing copied). Low and dark: a slow pulse in the bass (a low note on 1, a lower one on the
  // "and" of 3), open voicings that float in just after it, the minor line cliché (D–C♯–C–B) sliding inside the D minor
  // bars, the ♭II Lydian chord (E♭maj7♯11) for mystery and an altered A7 whose bass slips to E♭ (a tritone away) to pull
  // home. The right hand stays low (D4–F5), sparse, with long notes and space, echoing the sliding line from above.
  // 16 bars at 66 BPM, barely swung. Events are [midi, beat, length in beats, velocity]
  const UNDERTOW = (() => {
    const ev = [];
    const harmony = ['Dm', 'Dm', 'Eb', 'Eb', 'Dm', 'Dm', 'Bb', 'A7alt', 'Gm', 'Gm', 'Eb', 'Eb', 'Dm', 'Dm', 'Bb', 'A7sus'];
    const H = {                                            // [bass on 1, bass on the "and" of 3, the voicing above]
      Dm: [38, 33, [53, 57]],                              // F3 A3, with the sliding line added below
      Eb: [39, 34, [55, 57, 62]],                          // G A D: E♭maj7♯11, the ♯11 rubbing against the 3rd
      Bb: [34, 41, [57, 62, 64]],                          // A D E: B♭maj7♯11
      A7alt: [33, 39, [55, 61, 65]],                       // G C♯ F: A7♭13, the bass slipping to E♭
      Gm: [31, 38, [57, 60, 65]],                          // A C F: Gm11, rootless
      A7sus: [33, 40, [55, 58, 62]],                       // G B♭ D: A7sus♭9
    };
    const slide = [[62, 61], [60, 59]];                    // the line cliché over two bars of D minor: D, C♯ | C, B
    const tune = [                                         // per bar: [beat, midi, length]
      [[1.5, 69, 0.5], [2, 76, 1.5], [3.5, 74, 0.5]],
      [[0, 72, 1.5], [2, 71, 1], [3, 69, 0.5], [3.5, 65, 0.5]],
      [[1, 69, 1.5], [2.5, 70, 0.5], [3, 67, 1]],
      [[1, 74, 1.5], [2.5, 72, 0.5], [3, 69, 1]],
      [[1.5, 65, 0.5], [2, 69, 0.5], [2.5, 76, 1.5]],
      [[0, 74, 1], [1, 72, 1], [2, 71, 1.5]],
      [[0, 69, 1], [1, 76, 1], [2, 74, 0.5], [2.5, 72, 1.5]],
      [[0.5, 70, 0.5], [1, 73, 0.5], [1.5, 77, 1], [3, 73, 0.5], [3.5, 70, 0.5]],
      [[0, 69, 2], [2.5, 72, 0.5], [3, 74, 1]],
      [[0.5, 77, 1.5], [2, 74, 0.5], [2.5, 70, 1.5]],
      [[1, 69, 1], [2, 67, 0.5], [2.5, 70, 0.5], [3, 74, 1]],
      [[0, 72, 1.5], [1.5, 69, 2.5]],
      [[1.5, 65, 0.5], [2, 64, 1.5], [3.5, 69, 0.5]],
      [[0, 72, 1.5], [2, 71, 1], [3, 74, 1]],
      [[0, 76, 1.5], [1.5, 74, 0.5], [2, 69, 2]],
      [[1, 70, 0.5], [1.5, 69, 0.5], [2, 74, 1], [3, 76, 0.5], [3.5, 74, 0.5]],
    ];
    harmony.forEach((name, b) => {
      const [low, low2, voicing] = H[name], t = b * 4, first = harmony[b - 1] !== name;
      const lasts = harmony[b + 1] === name ? 8 : 4;       // a chord held for two bars rings for both
      ev.push([low, t, 2.45, 0.46], [low2, t + 2.5, 1.45, 0.34]);   // the pulse
      if (name === 'Dm') {
        if (first) voicing.forEach((n) => ev.push([n, t + 0.75, 7.2, 0.3]));
        slide[first ? 0 : 1].forEach((n, k) => ev.push([n, t + (k ? 2 : 0.75), k ? 2 : 1.25, 0.32]));
      } else if (first) {
        voicing.forEach((n, k) => ev.push([n, t + 0.75 + k * 0.03, lasts - 0.8, 0.3 - k * 0.02]));   // floats in after the bass
      } else voicing.forEach((n) => ev.push([n, t + 1.5, 2.4, 0.22]));   // a soft re-strike in a held chord's second bar
    });
    tune.forEach((notes, b) => notes.forEach(([at, n, d]) => ev.push([n, b * 4 + at, d, d >= 1 ? 0.58 : 0.5])));
    return ev;
  })();
  // the piano is real: the Salamander Grand Piano (a Yamaha C5, Alexander Holm, CC BY 3.0), 30 recorded notes a minor
  // third apart in assets/piano; each note plays the nearest recording, retuned — dry, no effects
  const PIANO = ['A0', ...[1, 2, 3, 4, 5, 6, 7].flatMap((o) => [`C${o}`, `Ds${o}`, `Fs${o}`, `A${o}`]), 'C8'];
  const pianoBufs = []; let pianoReady = null;
  const loadPiano = () => pianoReady || (pianoReady = Promise.all(PIANO.map(async (name) => {
    const [, pc, o] = name.match(/^([A-Z]s?)(\d)$/), n = 12 * (+o + 1) + { C: 0, Ds: 3, Fs: 6, A: 9 }[pc];
    const r = await fetch(`assets/piano/${name}.mp3`); pianoBufs.push([n, await ctx.decodeAudioData(await r.arrayBuffer())]);
  })));
  // the piece, rendered once on the real piano (dry, no effects): swung eighths, quick runs straight, a touch of human
  // timing; the last notes' ring is folded back onto the start so the loop is seamless, and it's brought to a set level
  async function renderPiece(score, bpm, swing, bars) {
    await loadPiano();
    const rate = ctx.sampleRate, beat = 60 / bpm, len = beat * 4 * bars, TAIL = 4;
    const oc = new OfflineAudioContext(2, Math.ceil((len + TAIL) * rate), rate);
    let seed = 20240607;
    const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
    const out = oc.createGain(); out.gain.value = 0.8; out.connect(oc.destination);
    const piano = (n, t, dur, vel) => {                    // the nearest recorded note, retuned; the damper falls at the note's end
      let near = pianoBufs[0]; for (const pb of pianoBufs) if (Math.abs(pb[0] - n) < Math.abs(near[0] - n)) near = pb;
      const b = oc.createBufferSource(), g = oc.createGain(), pan = oc.createStereoPanner();
      b.buffer = near[1]; b.playbackRate.value = Math.pow(2, (n - near[0]) / 12);
      g.gain.setValueAtTime(0.6 * vel, t); g.gain.setTargetAtTime(0, t + dur, 0.3);
      pan.pan.value = clamp((n - 64) / 30, -0.45, 0.45); b.connect(g); g.connect(pan); pan.connect(out);
      b.start(t); b.stop(t + dur + 2.5);
    };
    for (const [n, at, d, v] of score) {
      const swung = at % 1 === 0.5 && d >= 0.45;
      piano(n, Math.max(0, (at + (swung ? swing : 0)) * beat + (rnd() - 0.5) * 0.012), d * beat, clamp(v + (rnd() - 0.5) * 0.06, 0.1, 1));
    }
    const r = await oc.startRendering();
    const L = Math.ceil(len * rate), buf = ctx.createBuffer(2, L, rate); let peak = 0;
    for (let c = 0; c < 2; c++) {
      const a = r.getChannelData(c), d = buf.getChannelData(c);
      for (let i = 0; i < L; i++) d[i] = a[i] + (i + L < a.length ? a[i + L] : 0);
      for (let i = 0; i < L; i += 3) peak = Math.max(peak, Math.abs(d[i]));
    }
    const k = peak > 0 ? 0.8 / peak : 1;
    for (let c = 0; c < 2; c++) { const d = buf.getChannelData(c); for (let i = 0; i < L; i++) d[i] *= k; }
    return buf;
  }
