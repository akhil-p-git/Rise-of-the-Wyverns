"""Generates project-owned procedural placeholder SFX (WAV) and seamless looping
somber drones/ambience (OGG Vorbis via ffmpeg).

Loudness targets:
- Music: ~ -16 LUFS (seamless periodic harmonic synthesis)
- Ambience: ~ -22 LUFS (seamless periodic noise/harmonic synthesis)
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
    # Approximate K-weighted LUFS for mid/low-band drones & ambience
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
                "4",
                str(path),
            ],
            check=True,
        )


def periodic_colored_noise(
    rng: np.random.Generator, n: int, low_cut_bins: int, high_cut_bins: int
) -> np.ndarray:
    """Generates exactly periodic band-limited noise of length n (seamless loop)."""
    spec = np.zeros(n // 2 + 1, dtype=np.complex128)
    lo = max(1, low_cut_bins)
    hi = min(n // 2, high_cut_bins)
    phases = rng.uniform(0, 2 * np.pi, size=hi - lo)
    freqs = np.arange(lo, hi, dtype=np.float64)
    amps = 1.0 / np.sqrt(freqs)
    spec[lo:hi] = amps * np.exp(1j * phases)
    return np.fft.irfft(spec, n=n)


def gen_sfx() -> None:
    rng = np.random.default_rng(42)

    # 1. UI blips
    t = np.linspace(0, 0.045, int(SR * 0.045), endpoint=False)
    env = np.exp(-t * 65.0) * np.sin(np.pi * t / 0.045)
    ui_hover = np.sin(2 * np.pi * 310.0 * t) * env
    write_wav(SFX_DIR / "ui_hover.wav", normalize_peak(ui_hover) * 0.55)

    t = np.linspace(0, 0.11, int(SR * 0.11), endpoint=False)
    env = np.exp(-t * 28.0)
    ui_confirm = (
        0.65 * np.sin(2 * np.pi * 220.0 * t)
        + 0.35 * np.sin(2 * np.pi * 330.0 * t * np.where(t > 0.035, 1.0, 0.75))
    ) * env
    write_wav(SFX_DIR / "ui_confirm.wav", normalize_peak(ui_confirm))

    t = np.linspace(0, 0.10, int(SR * 0.10), endpoint=False)
    env = np.exp(-t * 32.0)
    freq_drop = np.linspace(260.0, 165.0, t.size)
    ui_back = np.sin(2 * np.pi * np.cumsum(freq_drop) / SR) * env
    write_wav(SFX_DIR / "ui_back.wav", normalize_peak(ui_back))

    t = np.linspace(0, 0.032, int(SR * 0.032), endpoint=False)
    env = np.exp(-t * 85.0)
    dlg_blip = (
        0.7 * np.sin(2 * np.pi * 245.0 * t) + 0.3 * np.sin(2 * np.pi * 490.0 * t)
    ) * env
    write_wav(SFX_DIR / "dialogue_blip.wav", normalize_peak(dlg_blip) * 0.45)

    # 2. Footsteps (sand, wet_sand, gravel, planks, stone)
    n_step = int(SR * 0.095)
    t_s = np.linspace(0, 0.095, n_step, endpoint=False)
    env_s = np.exp(-t_s * 34.0) * np.sin(np.pi * np.minimum(1.0, t_s / 0.015))

    sand = periodic_colored_noise(rng, n_step, 12, 160) * env_s
    write_wav(SFX_DIR / "step_sand.wav", normalize_peak(sand))

    wet_sand = periodic_colored_noise(rng, n_step, 18, 280) * env_s + 0.35 * np.sin(
        2 * np.pi * 120.0 * t_s
    ) * np.exp(-t_s * 50.0)
    write_wav(SFX_DIR / "step_wet_sand.wav", normalize_peak(wet_sand))

    gravel_bursts = (
        np.exp(-((t_s - 0.012) ** 2) / 0.00004)
        + 0.7 * np.exp(-((t_s - 0.034) ** 2) / 0.00005)
        + 0.4 * np.exp(-((t_s - 0.055) ** 2) / 0.00006)
    )
    gravel = periodic_colored_noise(rng, n_step, 25, 340) * gravel_bursts
    write_wav(SFX_DIR / "step_gravel.wav", normalize_peak(gravel))

    planks = (
        0.75 * np.sin(2 * np.pi * 105.0 * t_s) * np.exp(-t_s * 42.0)
        + 0.45 * np.sin(2 * np.pi * 195.0 * t_s) * np.exp(-t_s * 65.0)
        + 0.25 * periodic_colored_noise(rng, n_step, 8, 90) * env_s
    )
    write_wav(SFX_DIR / "step_planks.wav", normalize_peak(planks))

    stone = 0.5 * np.sin(2 * np.pi * 390.0 * t_s) * np.exp(
        -t_s * 85.0
    ) + 0.5 * periodic_colored_noise(rng, n_step, 40, 420) * np.exp(-t_s * 60.0)
    write_wav(SFX_DIR / "step_stone.wav", normalize_peak(stone))

    # 3. World interactions (pickup, rest_fire, scene_exit, thunder)
    t_p = np.linspace(0, 0.22, int(SR * 0.22), endpoint=False)
    pickup = 0.6 * np.sin(2 * np.pi * 293.66 * t_p) * np.exp(
        -t_p * 18.0
    ) + 0.5 * np.where(
        t_p >= 0.06, np.sin(2 * np.pi * 440.0 * (t_p - 0.06)), 0.0
    ) * np.exp(-np.maximum(0.0, t_p - 0.06) * 16.0)
    write_wav(SFX_DIR / "pickup.wav", normalize_peak(pickup))

    t_r = np.linspace(0, 0.55, int(SR * 0.55), endpoint=False)
    rest_fire = (
        0.5 * np.sin(2 * np.pi * 146.83 * t_r)
        + 0.35 * np.sin(2 * np.pi * 220.0 * t_r)
        + 0.25 * periodic_colored_noise(rng, t_r.size, 15, 220)
    ) * np.exp(-t_r * 5.0)
    write_wav(SFX_DIR / "rest_fire.wav", normalize_peak(rest_fire))

    t_e = np.linspace(0, 0.28, int(SR * 0.28), endpoint=False)
    scene_exit = (
        periodic_colored_noise(rng, t_e.size, 6, 85)
        * np.sin(np.pi * t_e / 0.28)
        * np.exp(-t_e * 6.0)
    )
    write_wav(SFX_DIR / "scene_exit.wav", normalize_peak(scene_exit))

    t_th = np.linspace(0, 0.9, int(SR * 0.9), endpoint=False)
    thunder = periodic_colored_noise(rng, t_th.size, 2, 110) * (
        0.8 * np.exp(-t_th * 3.5) + 0.4 * np.exp(-((t_th - 0.18) ** 2) / 0.02)
    )
    write_wav(SFX_DIR / "thunder.wav", normalize_peak(thunder))


def gen_ambience() -> None:
    rng = np.random.default_rng(108)
    n = SR * 6  # 6-second exact periodic loop
    t = np.linspace(0, 6.0, n, endpoint=False)

    # Waves: slow 6s swell modulating low coastal surf noise
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 6.0)
    waves = periodic_colored_noise(rng, n, 4, 180) * swell
    write_ogg_loop(AMB_DIR / "amb_waves.ogg", normalize_lufs(waves, -22.0))

    # Wind: eerie coastal wind with slow harmonic whistle
    wind_mod = 0.65 + 0.35 * np.sin(2 * np.pi * t / 6.0 + 1.1)
    wind = periodic_colored_noise(rng, n, 18, 120) * wind_mod
    write_ogg_loop(AMB_DIR / "amb_wind.ogg", normalize_lufs(wind, -23.0))

    # Rain: steady patter with high-mid band noise
    rain = periodic_colored_noise(rng, n, 60, 650) * (
        0.85 + 0.15 * np.sin(2 * np.pi * 2.0 * t / 6.0)
    )
    write_ogg_loop(AMB_DIR / "amb_rain.ogg", normalize_lufs(rain, -22.0))

    # Gulls: distant sparse coastal calls over soft air
    gulls = periodic_colored_noise(rng, n, 10, 80) * 0.15
    for call_t, f0 in ((1.4, 980.0), (1.85, 860.0), (4.2, 1020.0)):
        dt = t - call_t
        mask = (dt >= 0.0) & (dt < 0.32)
        dt_m = np.where(mask, dt, 0.0)
        pitch = f0 * (1.0 - 0.22 * (dt_m / 0.32))
        env = np.where(mask, np.sin(np.pi * dt_m / 0.32) * np.exp(-dt_m * 4.5), 0.0)
        gulls += 0.6 * np.sin(2 * np.pi * pitch * dt_m) * env
    write_ogg_loop(AMB_DIR / "amb_gulls.ogg", normalize_lufs(gulls, -24.0))

    # Fire crackle: warm low hearth rumble + periodic ember snaps
    fire = periodic_colored_noise(rng, n, 3, 95) * 0.45
    for snap_t in rng.uniform(0.1, 5.9, size=28):
        dt = np.abs(t - snap_t)
        snap_env = np.exp(-dt * 180.0)
        fire += periodic_colored_noise(rng, n, 150, 900) * snap_env * 1.4
    write_ogg_loop(AMB_DIR / "amb_fire.ogg", normalize_lufs(fire, -22.0))


def bowed_drone(
    t: np.ndarray,
    duration: float,
    root_hz: float,
    fifth_hz: float,
    minor_third_hz: float,
    pulse_cycles: int,
) -> np.ndarray:
    """Synthesises a seamless periodic bowed cello/viola drone with sparse hand-drum pulse."""
    sig = np.zeros_like(t)
    for k, amp in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.08)):
        # Ensure integer cycles over `duration` so loop is 100% phase-continuous
        c_root = max(1, round(root_hz * k * duration))
        c_fifth = max(1, round(fifth_hz * k * duration))
        c_third = max(1, round(minor_third_hz * k * duration))
        swell_a = 0.75 + 0.25 * np.sin(2 * np.pi * t / duration)
        swell_b = 0.70 + 0.30 * np.cos(2 * np.pi * t / duration)
        sig += amp * 0.55 * np.sin(2 * np.pi * c_root * t / duration) * swell_a
        sig += amp * 0.30 * np.sin(2 * np.pi * c_fifth * t / duration) * swell_b
        sig += amp * 0.18 * np.sin(2 * np.pi * c_third * t / duration)
    if pulse_cycles > 0:
        phase = (t * pulse_cycles / duration) % 1.0
        c_drum = max(1, round(55.0 * duration))
        drum = np.exp(-phase * 14.0) * np.sin(2 * np.pi * c_drum * t / duration)
        sig += 0.28 * drum
    return normalize_lufs(sig, -16.0)


def gen_music() -> None:
    dur = 8.0
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    # D minor / Dorian somber coastal drones (no heroic fanfare)
    write_ogg_loop(
        MUS_DIR / "mus_menu.ogg",
        bowed_drone(t, dur, 73.42, 110.0, 87.31, pulse_cycles=2),
    )
    write_ogg_loop(
        MUS_DIR / "mus_storm.ogg",
        bowed_drone(t, dur, 65.41, 98.0, 77.78, pulse_cycles=4),
    )
    write_ogg_loop(
        MUS_DIR / "mus_beach.ogg",
        bowed_drone(t, dur, 73.42, 110.0, 130.81, pulse_cycles=0),
    )
    write_ogg_loop(
        MUS_DIR / "mus_wrackmouth.ogg",
        bowed_drone(t, dur, 82.41, 123.47, 98.0, pulse_cycles=2),
    )
    write_ogg_loop(
        MUS_DIR / "mus_crossholm_road.ogg",
        bowed_drone(t, dur, 61.74, 92.50, 73.42, pulse_cycles=3),
    )


def main() -> None:
    gen_sfx()
    gen_ambience()
    gen_music()
    print("generated all audio cues under assets/audio/{sfx,ambience,music}")


if __name__ == "__main__":
    main()
