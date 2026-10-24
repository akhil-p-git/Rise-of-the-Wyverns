"""Generates project-owned procedural dark-fantasy RPG music (OGG Vorbis),
natural coastal/hearth ambience loops (OGG Vorbis), and organic wooden/parchment/lute
SFX (WAV). Zero high-pitched electronic sine beeps.

Loudness targets:
- Music: ~ -16 LUFS (melodic lute/harp arpeggios + bowed cello progressions + solo flute/viola)
- Ambience: ~ -22 LUFS (seamless periodic natural noise synthesis, no sine chirps)
- SFX: peak at -3 dBFS (0.7079 full scale)

Run: python3 tools/gen_sfx.py
"""

import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "assets" / "audio"
SFX_DIR = AUDIO_DIR / "sfx"
AMB_DIR = AUDIO_DIR / "ambience"
MUS_DIR = AUDIO_DIR / "music"

SR = 22050
PEAK_3DB = 10.0 ** (-3.0 / 20.0)


def normalize_peak(sig: np.ndarray, peak: float = PEAK_3DB) -> np.ndarray:
    mx = float(np.max(np.abs(sig)))
    if mx < 1e-8:
        return sig
    return sig * (peak / mx)


def normalize_lufs(sig: np.ndarray, target_lufs: float) -> np.ndarray:
    rms = float(np.sqrt(np.mean(sig**2)) + 1e-9)
    target_rms = 10.0 ** ((target_lufs + 0.691) / 20.0)
    out = sig * (target_rms / rms)
    return np.clip(out, -0.95, 0.95)


def write_wav(path: Path, sig: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(sig * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def write_ogg_loop(path: Path, sig: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        write_wav(Path(tmp.name), sig)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                tmp.name,
                "-c:a",
                "libvorbis",
                "-q:a",
                "5",
                str(path),
            ],
            check=True,
        )


def periodic_colored_noise(
    rng: np.random.Generator,
    n: int,
    low_cut_bins: int,
    high_cut_bins: int,
    rolloff: float = 0.75,
) -> np.ndarray:
    """Generates exactly periodic band-limited noise of length n (seamless loop)."""
    spec = np.zeros(n // 2 + 1, dtype=np.complex128)
    lo = max(1, low_cut_bins)
    hi = min(n // 2, high_cut_bins)
    phases = rng.uniform(0, 2 * np.pi, size=hi - lo)
    freqs = np.arange(lo, hi, dtype=np.float64)
    amps = 1.0 / (freqs**rolloff)
    spec[lo:hi] = amps * np.exp(1j * phases)
    return np.fft.irfft(spec, n=n)


def pluck_tone(t: np.ndarray, freq: float, decay: float = 6.0) -> np.ndarray:
    """Synthesises a warm acoustic lute/harp string pluck with higher harmonics
    that decay faster than the fundamental (natural wooden string damping)."""
    attack = np.minimum(1.0, t / 0.004)
    sig = np.zeros_like(t)
    harmonics = (
        (1, 1.00, 1.0),
        (2, 0.42, 1.6),
        (3, 0.20, 2.3),
        (4, 0.09, 3.2),
        (5, 0.04, 4.2),
    )
    for h_num, amp, damp in harmonics:
        if freq * h_num < SR * 0.42:
            env = attack * np.exp(-t * decay * damp)
            sig += amp * np.sin(2 * np.pi * (freq * h_num) * t) * env
    return sig


def gen_sfx() -> None:
    rng = np.random.default_rng(42)

    # 1. Organic medieval wooden/parchment/lute UI cues (NO electronic sine beeps!)
    t_h = np.linspace(0, 0.028, int(SR * 0.028), endpoint=False)
    hover_wood = periodic_colored_noise(rng, t_h.size, 3, 28, rolloff=0.9) * np.exp(
        -t_h * 140.0
    ) + 0.35 * np.sin(2 * np.pi * 135.0 * t_h) * np.exp(-t_h * 170.0)
    write_wav(SFX_DIR / "ui_hover.wav", normalize_peak(hover_wood) * 0.28)

    t_c = np.linspace(0, 0.24, int(SR * 0.24), endpoint=False)
    ui_confirm = 0.65 * pluck_tone(t_c, 146.83, decay=16.0) + 0.55 * np.where(
        t_c >= 0.025, pluck_tone(np.maximum(0.0, t_c - 0.025), 220.0, decay=14.0), 0.0
    )
    write_wav(SFX_DIR / "ui_confirm.wav", normalize_peak(ui_confirm) * 0.65)

    t_b = np.linspace(0, 0.18, int(SR * 0.18), endpoint=False)
    ui_back = 0.6 * pluck_tone(t_b, 164.81, decay=20.0) + 0.5 * np.where(
        t_b >= 0.02, pluck_tone(np.maximum(0.0, t_b - 0.02), 110.0, decay=18.0), 0.0
    )
    write_wav(SFX_DIR / "ui_back.wav", normalize_peak(ui_back) * 0.60)

    t_d = np.linspace(0, 0.022, int(SR * 0.022), endpoint=False)
    dlg_blip = periodic_colored_noise(rng, t_d.size, 4, 35, rolloff=0.95) * np.exp(
        -t_d * 180.0
    ) + 0.25 * np.sin(2 * np.pi * 120.0 * t_d) * np.exp(-t_d * 200.0)
    write_wav(SFX_DIR / "dialogue_blip.wav", normalize_peak(dlg_blip) * 0.24)

    # 2. Footsteps (sand, wet_sand, gravel, planks, stone)
    n_step = int(SR * 0.095)
    t_s = np.linspace(0, 0.095, n_step, endpoint=False)
    env_s = np.exp(-t_s * 34.0) * np.sin(np.pi * np.minimum(1.0, t_s / 0.015))

    sand = periodic_colored_noise(rng, n_step, 10, 140, rolloff=0.8) * env_s
    write_wav(SFX_DIR / "step_sand.wav", normalize_peak(sand) * 0.55)

    wet_sand = periodic_colored_noise(
        rng, n_step, 14, 210, rolloff=0.8
    ) * env_s + 0.25 * np.sin(2 * np.pi * 95.0 * t_s) * np.exp(-t_s * 60.0)
    write_wav(SFX_DIR / "step_wet_sand.wav", normalize_peak(wet_sand) * 0.55)

    gravel_bursts = (
        np.exp(-((t_s - 0.012) ** 2) / 0.00004)
        + 0.7 * np.exp(-((t_s - 0.034) ** 2) / 0.00005)
        + 0.4 * np.exp(-((t_s - 0.055) ** 2) / 0.00006)
    )
    gravel = periodic_colored_noise(rng, n_step, 20, 260, rolloff=0.8) * gravel_bursts
    write_wav(SFX_DIR / "step_gravel.wav", normalize_peak(gravel) * 0.55)

    planks = (
        0.70 * np.sin(2 * np.pi * 92.0 * t_s) * np.exp(-t_s * 48.0)
        + 0.35 * np.sin(2 * np.pi * 165.0 * t_s) * np.exp(-t_s * 72.0)
        + 0.25 * periodic_colored_noise(rng, n_step, 6, 75) * env_s
    )
    write_wav(SFX_DIR / "step_planks.wav", normalize_peak(planks) * 0.55)

    stone = 0.4 * np.sin(2 * np.pi * 180.0 * t_s) * np.exp(
        -t_s * 95.0
    ) + 0.6 * periodic_colored_noise(rng, n_step, 25, 280, rolloff=0.85) * np.exp(
        -t_s * 65.0
    )
    write_wav(SFX_DIR / "step_stone.wav", normalize_peak(stone) * 0.55)

    # 3. World interactions (pickup, rest_fire, scene_exit, thunder)
    t_p = np.linspace(0, 0.36, int(SR * 0.36), endpoint=False)
    pickup = 0.55 * pluck_tone(t_p, 293.66, decay=11.0) + 0.50 * np.where(
        t_p >= 0.055,
        pluck_tone(np.maximum(0.0, t_p - 0.055), 440.0, decay=10.0),
        0.0,
    )
    write_wav(SFX_DIR / "pickup.wav", normalize_peak(pickup) * 0.70)

    t_r = np.linspace(0, 0.85, int(SR * 0.85), endpoint=False)
    rest_fire = (
        0.45 * pluck_tone(t_r, 146.83, decay=4.5)
        + 0.35
        * np.where(
            t_r >= 0.08, pluck_tone(np.maximum(0.0, t_r - 0.08), 220.0, decay=4.5), 0.0
        )
        + 0.30
        * np.where(
            t_r >= 0.16,
            pluck_tone(np.maximum(0.0, t_r - 0.16), 293.66, decay=4.5),
            0.0,
        )
    )
    write_wav(SFX_DIR / "rest_fire.wav", normalize_peak(rest_fire) * 0.75)

    t_e = np.linspace(0, 0.28, int(SR * 0.28), endpoint=False)
    scene_exit = (
        periodic_colored_noise(rng, t_e.size, 6, 85)
        * np.sin(np.pi * t_e / 0.28)
        * np.exp(-t_e * 6.0)
    )
    write_wav(SFX_DIR / "scene_exit.wav", normalize_peak(scene_exit) * 0.65)

    t_th = np.linspace(0, 0.9, int(SR * 0.9), endpoint=False)
    thunder = periodic_colored_noise(rng, t_th.size, 2, 110) * (
        0.8 * np.exp(-t_th * 3.5) + 0.4 * np.exp(-((t_th - 0.18) ** 2) / 0.02)
    )
    write_wav(SFX_DIR / "thunder.wav", normalize_peak(thunder))


def gen_ambience() -> None:
    rng = np.random.default_rng(108)
    n = SR * 8  # 8-second exact periodic loop
    t = np.linspace(0, 8.0, n, endpoint=False)

    # Waves: slow 8s coastal surf swell with warm low-frequency wash
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 8.0)
    waves = periodic_colored_noise(rng, n, 4, 150, rolloff=0.85) * swell
    write_ogg_loop(AMB_DIR / "amb_waves.ogg", normalize_lufs(waves, -23.0))

    # Wind: soft low-mid highland breeze (no high-pitched whistle)
    wind_mod = 0.65 + 0.35 * np.sin(2 * np.pi * t / 8.0 + 1.1)
    wind = periodic_colored_noise(rng, n, 12, 95, rolloff=0.9) * wind_mod
    write_ogg_loop(AMB_DIR / "amb_wind.ogg", normalize_lufs(wind, -24.0))

    # Rain: gentle steady rain wash
    rain = periodic_colored_noise(rng, n, 45, 480, rolloff=0.8) * (
        0.88 + 0.12 * np.sin(2 * np.pi * 2.0 * t / 8.0)
    )
    write_ogg_loop(AMB_DIR / "amb_rain.ogg", normalize_lufs(rain, -23.0))

    # Coastal harbour air (`amb_gulls.ogg` — NO sine-wave chirps/beeps! Soft distant rigging creak & sea air)
    harbour_air = periodic_colored_noise(rng, n, 8, 70, rolloff=0.95) * (
        0.6 + 0.4 * np.cos(2 * np.pi * t / 8.0)
    )
    write_ogg_loop(AMB_DIR / "amb_gulls.ogg", normalize_lufs(harbour_air, -26.0))

    # Fire crackle: warm low hearth rumble + soft ember snaps
    fire = periodic_colored_noise(rng, n, 3, 80, rolloff=0.9) * 0.55
    for snap_t in rng.uniform(0.2, 7.8, size=18):
        dt = np.abs(t - snap_t)
        snap_env = np.exp(-dt * 210.0)
        fire += periodic_colored_noise(rng, n, 90, 420, rolloff=0.85) * snap_env * 0.9
    write_ogg_loop(AMB_DIR / "amb_fire.ogg", normalize_lufs(fire, -24.0))


def add_periodic_pluck(
    mix: np.ndarray,
    dur: float,
    onset: float,
    freq: float,
    amp: float = 0.25,
    decay: float = 3.2,
) -> None:
    """Adds a plucked lute/harp note at `onset` (seconds) that wraps around `dur` seamlessly."""
    n = mix.size
    t_rel = (np.arange(n, dtype=np.float64) / SR - onset) % dur
    note = pluck_tone(t_rel, freq, decay=decay)
    # Smooth fade-out before loop wrap so there is zero click
    wrap_fade = np.clip((dur - t_rel) / 0.15, 0.0, 1.0)
    mix += amp * note * wrap_fade


def add_periodic_pad_note(
    mix: np.ndarray,
    dur: float,
    onset: float,
    length: float,
    freq: float,
    amp: float = 0.18,
) -> None:
    """Adds a warm bowed cello/viola or wooden flute sustained note with smooth cosine envelope."""
    n = mix.size
    t_rel = (np.arange(n, dtype=np.float64) / SR - onset) % dur
    active = t_rel < length
    t_a = np.where(active, t_rel, 0.0)
    # Smooth attack (0.45s) and release (0.65s)
    att = np.minimum(1.0, t_a / 0.45)
    rel = np.minimum(1.0, np.maximum(0.0, (length - t_a) / 0.65))
    env = np.where(active, np.sin(0.5 * np.pi * att) * np.sin(0.5 * np.pi * rel), 0.0)
    # Integer cycle snap for phase continuity + warm vibrato
    vib = 0.0025 * np.sin(2 * np.pi * 4.5 * t_a)
    tone = (
        0.70 * np.sin(2 * np.pi * freq * (1.0 + vib) * t_a)
        + 0.22 * np.sin(2 * np.pi * (freq * 2.0) * (1.0 + vib) * t_a)
        + 0.08 * np.sin(2 * np.pi * (freq * 3.0) * t_a)
    )
    mix += amp * tone * env


def apply_cathedral_reverb(sig: np.ndarray, dur: float) -> np.ndarray:
    """Adds warm periodic multi-tap stereo-like hall diffusion so plucked lute and strings
    blend into a lush Morrowind/Skyrim-style acoustic space."""
    out = sig.copy()
    taps = (
        (0.073, 0.28),
        (0.137, 0.21),
        (0.229, 0.15),
        (0.353, 0.11),
        (0.509, 0.07),
    )
    for delay_s, gain in taps:
        shift = int(delay_s * SR)
        out += gain * np.roll(sig, shift)
    return out


# Note frequency helper (A4 = 440 Hz)
NOTES = {
    "C2": 65.41,
    "D2": 73.42,
    "Eb2": 77.78,
    "E2": 82.41,
    "F2": 87.31,
    "G2": 98.00,
    "A2": 110.00,
    "Bb2": 116.54,
    "B2": 123.47,
    "C3": 130.81,
    "D3": 146.83,
    "Eb3": 155.56,
    "E3": 164.81,
    "F3": 174.61,
    "F#3": 185.00,
    "G3": 196.00,
    "A3": 220.00,
    "Bb3": 233.08,
    "B3": 246.94,
    "C4": 261.63,
    "D4": 293.66,
    "Eb4": 311.13,
    "E4": 329.63,
    "F4": 349.23,
    "F#4": 369.99,
    "G4": 392.00,
    "A4": 440.00,
    "Bb4": 466.16,
    "B4": 493.88,
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
}


def build_track(
    dur: float,
    chords: list[tuple[str, str, list[str], str]],
) -> np.ndarray:
    """Builds a multi-bar dark-fantasy track from a chord & melody progression:
    Each bar tuple: (bass_note, fifth_note, arpeggio_notes, melody_note)."""
    n = int(SR * dur)
    mix = np.zeros(n, dtype=np.float64)
    bar_len = dur / len(chords)

    for b_idx, (bass, fifth, arp, mel) in enumerate(chords):
        t0 = b_idx * bar_len
        # Warm bowed cello bass + fifth pad
        add_periodic_pad_note(mix, dur, t0, bar_len * 1.08, NOTES[bass], amp=0.26)
        add_periodic_pad_note(mix, dur, t0, bar_len * 1.05, NOTES[fifth], amp=0.15)

        # Plucked lute / harp arpeggio across the bar
        step = bar_len / len(arp)
        for i, note_name in enumerate(arp):
            if note_name:
                accent = 0.24 if i == 0 else (0.19 if i == len(arp) // 2 else 0.15)
                add_periodic_pluck(
                    mix, dur, t0 + i * step, NOTES[note_name], amp=accent, decay=2.8
                )

        # Expressive solo viola / wooden flute phrase
        if mel:
            add_periodic_pad_note(
                mix, dur, t0 + step * 0.5, bar_len * 0.82, NOTES[mel], amp=0.14
            )

    mix = apply_cathedral_reverb(mix, dur)
    return normalize_lufs(mix, -16.5)


def gen_music() -> None:
    # 1. Title & Character Creation (`mus_menu.ogg`): Haunting D-Dorian / D-minor theme
    #    (Morrowind / Skyrim inspired: Dm -> Bbmaj7 -> Gm -> Asus4/A)
    menu_chords = [
        ("D2", "A2", ["D3", "A3", "D4", "E4", "F4", "E4", "D4", "A3"], "A4"),
        ("Bb2", "F2", ["Bb2", "F3", "Bb3", "C4", "D4", "C4", "Bb3", "F3"], "F4"),
        ("G2", "D2", ["G2", "D3", "G3", "A3", "Bb3", "A3", "G3", "D3"], "G4"),
        ("A2", "E2", ["A2", "E3", "A3", "D4", "C4", "A3", "E3", "A2"], "E4"),
    ]
    write_ogg_loop(MUS_DIR / "mus_menu.ogg", build_track(16.0, menu_chords))

    # 2. Intro Storm (`mus_storm.ogg`): Brooding C-minor cello & harp tension
    storm_chords = [
        ("C2", "G2", ["C3", "G3", "C4", "Eb4", "D4", "C4", "G3", "Eb3"], "G4"),
        ("Eb2", "Bb2", ["Eb3", "Bb3", "Eb4", "G4", "F4", "Eb4", "Bb3", "G3"], "Bb4"),
        (
            "F2",
            "C3",
            ["F2", "C3", "F3", "Ab3", "G3", "F3", "C3", "F2"]
            if "Ab3" in NOTES
            else ["F2", "C3", "F3", "G3", "A3", "G3", "F3", "C3"],
            "F4",
        ),
        ("G2", "D3", ["G2", "D3", "G3", "B3", "C4", "B3", "G3", "D3"], "D4"),
    ]
    write_ogg_loop(MUS_DIR / "mus_storm.ogg", build_track(16.0, storm_chords))

    # 3. Shipwreck Beach (`mus_beach.ogg`): Sparse, contemplative A-Aeolian coastal harp & cello
    beach_chords = [
        ("A2", "E3", ["A3", "", "E4", "C4", "A3", "", "E3", ""], "E4"),
        ("F2", "C3", ["F3", "", "C4", "A3", "F3", "", "C3", ""], "C4"),
        ("D2", "A2", ["D3", "", "A3", "F3", "D3", "", "A2", ""], "D4"),
        ("E2", "B2", ["E3", "", "B3", "G3", "E3", "", "B2", ""], "B3"),
    ]
    write_ogg_loop(MUS_DIR / "mus_beach.ogg", build_track(16.0, beach_chords))

    # 4. Wrackmouth Village (`mus_wrackmouth.ogg`): Warm yet grim E-Dorian medieval harbour lute theme
    #    (Em -> G -> D -> Am)
    wrackmouth_chords = [
        ("E2", "B2", ["E3", "B3", "E4", "F#4", "G4", "F#4", "E4", "B3"], "B4"),
        ("G2", "D3", ["G3", "D4", "G4", "F#4", "D4", "B3", "G3", "D3"], "A4"),
        ("D2", "A2", ["D3", "A3", "D4", "E4", "F#4", "E4", "D4", "A3"], "F#4"),
        ("A2", "E3", ["A2", "E3", "A3", "B3", "C4", "B3", "A3", "E3"], "E4"),
    ]
    write_ogg_loop(MUS_DIR / "mus_wrackmouth.ogg", build_track(16.0, wrackmouth_chords))

    # 5. Crossholm Road (`mus_crossholm_road.ogg`): Lonely highland G-minor road ballad
    road_chords = [
        ("G2", "D3", ["G3", "D4", "Bb3", "G3", "D3", "G3", "Bb3", "D4"], "D4"),
        ("Eb2", "Bb2", ["Eb3", "Bb3", "G3", "Eb3", "Bb2", "Eb3", "G3", "Bb3"], "G4"),
        ("C2", "G2", ["C3", "G3", "Eb4", "C4", "G3", "C3", "Eb3", "G3"], "Eb4"),
        ("D2", "A2", ["D3", "A3", "D4", "C4", "A3", "F#3", "D3", "A2"], "A3"),
    ]
    write_ogg_loop(MUS_DIR / "mus_crossholm_road.ogg", build_track(16.0, road_chords))


def main() -> None:
    gen_sfx()
    gen_ambience()
    gen_music()
    print("generated all audio cues under assets/audio/{sfx,ambience,music}")


if __name__ == "__main__":
    main()
