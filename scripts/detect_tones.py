#!/usr/bin/env python3

"""
detect_tones_chunked.py

Scans a long audio file for high-amplitude ~1000 Hz tones (typically
0.5-2 seconds long), even in the presence of speech or other audio.

Method:
- Processes audio in chunks to avoid loading the full file into memory.
- Uses a spectrogram (FFT over time) to measure energy near 1000 Hz.
- Declares a tone only when BOTH are true:
    1. The 1000 Hz band is much louder than broadband background
       (threshold test)
    2. The 1000 Hz band dominates neighboring frequencies
       (narrowband purity test, helps reject speech)

- Filters out detections shorter than a minimum duration.
- Uses overlapping chunks so tones crossing chunk boundaries are not missed.
- Merges adjacent detections separated by small gaps.

Output:
- Prints detected tone intervals as:

    HH:MM:SS - HH:MM:SS  duration=X.XXXs

Example:

    00:12:41 - 00:12:42 duration=1.03s

Usage:

    python3 detect_tones_chunked.py audio.wav \
      --threshold 30 \
      --purity-threshold 8

Dependencies:
    pip install numpy soundfile scipy
"""

#!/usr/bin/env python3

import argparse
import numpy as np
import soundfile as sf
from scipy.signal import spectrogram


def fmt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def merge_segments(segments, gap):
    if not segments:
        return []

    segments.sort()
    merged = [segments[0]]

    for start, end in segments[1:]:
        prev_start, prev_end = merged[-1]

        if start - prev_end <= gap:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


def detect_in_chunk(
    audio,
    sr,
    chunk_start_sec,
    freq=1000,
    threshold=25.0,
    purity_threshold=6.0,
    min_duration=0.45,
):
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    freqs, times, S = spectrogram(
        audio,
        fs=sr,
        window="hann",
        nperseg=2048,
        noverlap=1536,
        scaling="spectrum",
        mode="magnitude",
    )

    target_bins = (freqs >= freq - 20) & (freqs <= freq + 20)
    lower_bins = (freqs >= freq - 180) & (freqs <= freq - 60)
    upper_bins = (freqs >= freq + 60) & (freqs <= freq + 180)

    if not np.any(target_bins):
        return []

    target = S[target_bins, :].mean(axis=0)
    lower = S[lower_bins, :].mean(axis=0)
    upper = S[upper_bins, :].mean(axis=0)
    nearby = ((lower + upper) / 2.0) + 1e-12
    broadband = np.median(S, axis=0) + 1e-12

    loud_enough = target / broadband > threshold
    narrow_enough = target / nearby > purity_threshold
    active = loud_enough & narrow_enough

    segments = []
    start = None

    for i, is_active in enumerate(active):
        t = chunk_start_sec + times[i]

        if is_active and start is None:
            start = t
        elif not is_active and start is not None:
            end = t
            if end - start >= min_duration:
                segments.append((start, end))
            start = None

    if start is not None:
        end = chunk_start_sec + times[-1]
        if end - start >= min_duration:
            segments.append((start, end))

    return segments


def detect_tones_chunked(
    path,
    freq=1000,
    threshold=25.0,
    purity_threshold=6.0,
    min_duration=0.45,
    merge_gap=0.25,
    chunk_seconds=30,
    overlap_seconds=2,
):
    all_segments = []

    with sf.SoundFile(path) as f:
        sr = f.samplerate
        chunk_frames = int(chunk_seconds * sr)
        overlap_frames = int(overlap_seconds * sr)

        pos = 0
        total_frames = len(f)

        while pos < total_frames:
            f.seek(pos)
            frames_to_read = min(chunk_frames + overlap_frames, total_frames - pos)
            audio = f.read(frames_to_read, dtype="float32")

            chunk_start_sec = pos / sr

            segments = detect_in_chunk(
                audio,
                sr,
                chunk_start_sec,
                freq=freq,
                threshold=threshold,
                purity_threshold=purity_threshold,
                min_duration=min_duration,
            )

            all_segments.extend(segments)

            pos += chunk_frames

    return merge_segments(all_segments, merge_gap)


def main():
    parser = argparse.ArgumentParser(
        description="Memory-efficient 1000Hz tone detector."
    )

    parser.add_argument("audio_file")
    parser.add_argument("--freq", type=float, default=1000)
    parser.add_argument("--threshold", type=float, default=25.0)
    parser.add_argument("--purity-threshold", type=float, default=6.0)
    parser.add_argument("--min-duration", type=float, default=0.45)
    parser.add_argument("--merge-gap", type=float, default=0.25)
    parser.add_argument("--chunk-seconds", type=float, default=30)
    parser.add_argument("--overlap-seconds", type=float, default=2)

    args = parser.parse_args()

    segments = detect_tones_chunked(
        args.audio_file,
        freq=args.freq,
        threshold=args.threshold,
        purity_threshold=args.purity_threshold,
        min_duration=args.min_duration,
        merge_gap=args.merge_gap,
        chunk_seconds=args.chunk_seconds,
        overlap_seconds=args.overlap_seconds,
    )

    for start, end in segments:
        print(f"{fmt_time(start)},{fmt_time(end)},{end - start:.3f}s")


if __name__ == "__main__":
    main()
