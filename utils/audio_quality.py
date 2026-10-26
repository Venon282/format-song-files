"""
audio_quality.py - objective sound-quality measurement, to pick the best of several duplicates.

Principle
---------
When two files contain the *same* recording, any difference in quality comes from
the encoding chain. So we measure facts, not tastes:

1. Effective bandwidth: the frequency above which there is no more signal.
   Every lossy encoder cuts the highs at a frequency that depends on its bitrate
   (MP3 128k ~16 kHz, MP3 320k ~20 kHz, AAC ~17 kHz, Opus/Vorbis ~20 kHz...).
   It is measured on the decoded signal, so it cannot be faked: a 128k MP3
   re-encoded to FLAC or to a "320k" MP3 keeps its 16 kHz cutoff.
2. Coding fidelity: genuine lossless, or the real audio bitrate weighted by the
   codec's efficiency (128 kbps Opus != 128 kbps MP3).
3. Integrity: clipping (waveforms flattened at 0 dBFS) and overshoots above 0 dBFS.

What this module does NOT measure: mastering differences (EQ, compression,
remasters), which are a matter of taste rather than a measurable defect.

Requirements: numpy, plus ffmpeg and ffprobe in the PATH (or change FFMPEG / FFPROBE).

Usage
-----
    from audio_quality import rankAudioQuality

    ranking, decisive = rankAudioQuality([path_a, path_b])
    best = ranking[0]
    print(best.path, best.score, decisive)

    python audio_quality.py file1.mp3 file2.opus ...
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field

import numpy as np

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

# --- Analysis parameters (tunable) ------------------------------------------
_ANALYSIS_SR = 48_000          # decoding sample rate, shared by every file
_NFFT = 8192                   # spectral resolution ~5.9 Hz
_BANDWIDTH_REF_HZ = 20_000     # above this, human hearing no longer tells the difference
_DYNAMIC_RANGE_DB = 65.0       # "there is signal" = less than 65 dB below the mid-band
_CLIFF_DB = 30.0               # sharp drop typical of a lossy encoder's lowpass filter
_TRANSCODE_MAX_CUTOFF_HZ = 19_000
_FLAT_RUN_MIN = 4              # >= 4 consecutive samples at the ceiling = clipping
_CLIP_FULL_PENALTY = 0.005     # 0.5 % clipped samples = maximum penalty
_CLIP_MAX_PENALTY = 0.5        # maximum clipping removes up to 50 % of the score
_TRANSCODE_FIDELITY = 0.45     # a "lossless" made from a lossy is worth an average lossy
_LOSSY_FIDELITY_MAX = 0.85     # a lossy file never reaches a genuine lossless one
_LOSSY_FIDELITY_REF_KBPS = 256

_WEIGHTS = {"bandwidth": 0.55, "fidelity": 0.45}

_LOSSLESS_CODECS = {
    "flac", "alac", "wavpack", "ape", "tta", "tak", "mlp", "truehd", "shorten",
}
# "MP3-equivalent" bitrate: at equal bitrate, these codecs sound better than MP3.
# Rules of thumb drawn from public listening tests, used only to weight the
# bitrate, never to decide on their own.
_CODEC_EFFICIENCY = {"mp3": 1.0, "aac": 1.4, "vorbis": 1.3, "opus": 1.6}

# Typical LAME lowpass (the most widespread MP3 encoder) by CBR bitrate.
# Used to expose a "320k" MP3 re-encoded from a 128k one: its advertised bitrate
# lies, but its ~17 kHz cutoff stays that of the original 128k file.
_MP3_LOWPASS_HZ = (11_000, 15_000, 16_500, 17_500, 18_900, 19_700, 20_200)
_MP3_LOWPASS_KBPS = (64, 96, 128, 160, 192, 256, 320)


@dataclass
class AudioQuality:
    path: str
    codec: str
    lossless: bool
    sample_rate: int
    channels: int
    duration: float
    bitrate_kbps: float          # real audio bitrate (excludes cover art and tags)
    cutoff_hz: float             # effective bandwidth
    cliff_db: float              # sharpness of the cutoff (encoder filter)
    transcode_suspected: bool    # lossless container, but the signal comes from a lossy source
    clipping_ratio: float        # share of clipped samples / samples above 0 dBFS
    score: float = 0.0           # 0-100, indicative; only compare duplicates with each other
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Reading the file
# ---------------------------------------------------------------------------
def _run(cmd: list[str], text: bool = True) -> subprocess.CompletedProcess:
    kwargs = {"encoding": "utf-8", "errors": "replace"} if text else {}
    return subprocess.run(cmd, capture_output=True, check=True, text=text, **kwargs)


def _probe(path: str) -> tuple[str, int, int, int]:
    """Return (codec, sample_rate, channels, real audio bytes)."""
    info = json.loads(_run([
        FFPROBE, "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels",
        "-of", "json", path,
    ]).stdout)
    streams = info.get("streams") or []
    if not streams:
        raise ValueError(f"No audio stream in: {path}")
    s = streams[0]

    # Sum of the audio packets: excludes cover art, tags and headers, unlike the
    # container bitrate, which is skewed by a 500 KB picture in the comments.
    packets = _run([
        FFPROBE, "-v", "error", "-select_streams", "a:0",
        "-show_entries", "packet=size", "-of", "csv=p=0", path,
    ]).stdout
    audio_bytes = sum(int(t.strip(",")) for t in packets.split() if t.strip(",").isdigit())

    return (
        s.get("codec_name", "unknown"),
        int(s.get("sample_rate", 0) or 0),
        int(s.get("channels", 0) or 0),
        audio_bytes,
    )


def _decode(path: str) -> np.ndarray:
    """Decode to 48 kHz stereo float32: array of shape (n, 2)."""
    raw = _run([
        FFMPEG, "-v", "error", "-nostdin", "-i", path,
        "-map", "0:a:0", "-vn", "-ac", "2", "-ar", str(_ANALYSIS_SR),
        "-f", "f32le", "pipe:1",
    ], text=False).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------
def _averageSpectrumDb(mono: np.ndarray) -> np.ndarray:
    """Average power spectrum over the whole track, in dB."""
    hop = _NFFT // 2
    n_frames = 1 + (len(mono) - _NFFT) // hop
    window = np.blackman(_NFFT).astype(np.float32)
    offsets = np.arange(_NFFT)
    acc = np.zeros(_NFFT // 2 + 1)
    for i in range(0, n_frames, 256):          # in batches: constant memory
        starts = np.arange(i, min(i + 256, n_frames)) * hop
        frames = mono[starts[:, None] + offsets] * window
        acc += (np.abs(np.fft.rfft(frames, axis=1)) ** 2).sum(axis=0)
    return 10 * np.log10(acc / n_frames + 1e-20)


def _medianFilter(a: np.ndarray, width: int) -> np.ndarray:
    """Sliding median: removes narrow spikes (whistles, spurious tones)."""
    padded = np.pad(a, width // 2, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, width)
    return np.median(windows, axis=1)[: len(a)]


def _cliffCurve(smooth: np.ndarray) -> np.ndarray:
    """For each frequency: mean level just below it minus mean level just above it."""
    df = _ANALYSIS_SR / _NFFT
    near, far = round(200 / df), round(1000 / df)
    prefix = np.concatenate(([0.0], np.cumsum(smooth)))
    n = len(smooth)
    drop = np.zeros(n)
    i = np.arange(far, n - far)
    below = (prefix[i - near] - prefix[i - far]) / (far - near)
    above = (prefix[i + far] - prefix[i + near]) / (far - near)
    drop[i] = below - above
    return drop


def _estimateBandwidth(mono: np.ndarray) -> tuple[float, float]:
    """Return (cutoff frequency in Hz, drop in dB at that cutoff)."""
    freqs = np.fft.rfftfreq(_NFFT, 1 / _ANALYSIS_SR)
    smooth = _medianFilter(_averageSpectrumDb(mono), 41)   # ~240 Hz

    ref = float(np.median(smooth[(freqs >= 1000) & (freqs <= 4000)]))
    if ref < -120:                                          # digital silence
        return 0.0, 0.0

    # a) last frequency where audible signal remains (< 65 dB below the mid-band)
    threshold = ref - _DYNAMIC_RANGE_DB
    in_range = (freqs >= 4000) & (freqs <= 22_000)
    above = np.flatnonzero(in_range & (smooth >= threshold))
    cutoff_idx = int(above.max()) if above.size else int(np.searchsorted(freqs, 4000))

    # b) sharp cliff (encoder filter): more reliable than the threshold when the
    #    encoder leaves residual noise above its cutoff (AAC, low-bitrate Opus)
    drop = _cliffCurve(smooth)
    cliff_range = np.flatnonzero((freqs >= 6000) & (freqs <= 22_000))
    best = cliff_range[int(np.argmax(drop[cliff_range]))]
    if drop[best] >= _CLIFF_DB and best < cutoff_idx:
        cutoff_idx = int(best)

    return float(freqs[cutoff_idx]), float(drop[cutoff_idx])


def _clippingRatio(stereo: np.ndarray) -> float:
    """Share of samples flattened at the ceiling (>= 4 in a row) or above 0 dBFS."""
    peak = float(np.abs(stereo).max())
    if peak < 0.05:
        return 0.0

    worst = 0.0
    for ch in range(stereo.shape[1]):
        x = np.abs(stereo[:, ch])
        mask = (x >= 0.999 * peak).astype(np.int8)
        edges = np.diff(np.concatenate(([0], mask, [0])))
        runs = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
        flat = runs[runs >= _FLAT_RUN_MIN].sum() / len(x)
        overs = float((x > 1.0).mean())
        worst = max(worst, flat + overs)
    return worst


def _fidelity(codec: str, lossless: bool, transcode: bool,
              bitrate_kbps: float, cutoff_hz: float, cliff_db: float) -> float:
    if lossless:
        return _TRANSCODE_FIDELITY if transcode else 1.0

    # MP3 whose sharp cutoff proves a source bitrate lower than the advertised one
    if codec == "mp3" and cliff_db >= _CLIFF_DB:
        proven = float(np.interp(cutoff_hz, _MP3_LOWPASS_HZ, _MP3_LOWPASS_KBPS))
        bitrate_kbps = min(bitrate_kbps, proven)

    effective = bitrate_kbps * _CODEC_EFFICIENCY.get(codec, 1.0)
    return min(_LOSSY_FIDELITY_MAX,
               _LOSSY_FIDELITY_MAX * effective / _LOSSY_FIDELITY_REF_KBPS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def analyzeAudioQuality(path: str) -> AudioQuality:
    """Measure the quality of one audio file (full analysis, ~1-3 s)."""
    codec, sample_rate, channels, audio_bytes = _probe(path)
    stereo = _decode(path)
    if len(stereo) < _NFFT * 2:
        raise ValueError(f"File too short to analyze: {path}")

    duration = len(stereo) / _ANALYSIS_SR
    lossless = codec in _LOSSLESS_CODECS or codec.startswith("pcm_")
    bitrate = audio_bytes * 8 / duration / 1000

    cutoff, cliff = _estimateBandwidth(stereo.mean(axis=1))
    transcode = (lossless
                 and cutoff < _TRANSCODE_MAX_CUTOFF_HZ
                 and cliff >= _CLIFF_DB)
    clipping = _clippingRatio(stereo)

    bandwidth = min(cutoff, _BANDWIDTH_REF_HZ) / _BANDWIDTH_REF_HZ
    fidelity = _fidelity(codec, lossless, transcode, bitrate, cutoff, cliff)
    base = 100 * (_WEIGHTS["bandwidth"] * bandwidth + _WEIGHTS["fidelity"] * fidelity)
    clip_severity = min(1.0, clipping / _CLIP_FULL_PENALTY)
    score = base * (1.0 - _CLIP_MAX_PENALTY * clip_severity)

    notes = []
    if transcode:
        notes.append(f"probable fake lossless: sharp cutoff at {cutoff / 1000:.1f} kHz "
                     f"({cliff:.0f} dB drop), typical of a lossy encoder")
    elif 0 < cutoff < 18_000:
        notes.append(f"bandwidth limited to {cutoff / 1000:.1f} kHz")
    if clipping >= 0.0002:
        notes.append(f"clipping detected ({clipping * 100:.2f} % of samples)")
    if cutoff == 0.0:
        notes.append("near-silent signal: measurement not reliable")

    return AudioQuality(
        path=path, codec=codec, lossless=lossless, sample_rate=sample_rate,
        channels=channels, duration=duration, bitrate_kbps=bitrate,
        cutoff_hz=cutoff, cliff_db=cliff, transcode_suspected=transcode,
        clipping_ratio=clipping, score=score, notes=notes,
    )


def rankAudioQuality(
    paths: list[str] | tuple[str, ...],
    min_margin: float = 3.0,
    keep_order:bool = True,
) -> tuple[list[AudioQuality], bool]:
    """
    Rank n files from best to worst.

    Returns (ranking, decisive). `decisive` is False when the score gap between
    the top two files is below `min_margin` points: the files are then
    technically equivalent and the measurement cannot pick a winner
    (your call, or keep the lighter file).
    """
    if not paths:
        raise ValueError("No files to compare.")

    results = [analyzeAudioQuality(p) for p in paths]
    
    if keep_order is False:
        results.sort(key=lambda r: r.score, reverse=True)

    durations = [r.duration for r in results]
    if max(durations) - min(durations) > 2.0:
        for r in results:
            r.notes.append("durations differ between duplicates (intro/outro?), "
                           "interpret the comparison with caution")

    decisive = len(results) == 1 or (results[0].score - results[1].score) >= min_margin
    return results, decisive


def pickBestAudio(paths: list[str] | tuple[str, ...],
                  min_margin: float = 3.0) -> tuple[str, bool]:
    """Shortcut: (path of the best file, whether the measurement is decisive)."""
    ranking, decisive = rankAudioQuality(paths, min_margin)
    return ranking[0].path, decisive


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Usage: python audio_quality.py file1 file2 [file3 ...]")

    ranking, decisive = rankAudioQuality(sys.argv[1:])
    print(f"{'#':>2} {'score':>6} {'codec':<8} {'kbps':>6} {'cutoff':>9} "
          f"{'clip':>7}  file")
    for i, r in enumerate(ranking, 1):
        print(f"{i:>2} {r.score:6.1f} {r.codec:<8} {r.bitrate_kbps:6.0f} "
              f"{r.cutoff_hz / 1000:7.1f} k {r.clipping_ratio * 100:6.2f}%  {r.path}")
        for note in r.notes:
            print(f"{'':>2} -> {note}")
    print("\nVerdict:", "decisive" if decisive
          else "TECHNICAL TIE, the measurement cannot pick a winner")