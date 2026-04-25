#!/usr/bin/env python3
import sys
import numpy as np
import wave

labels_file = sys.argv[1]
out_wav = sys.argv[2]

sample_rate = 48000
tone_freq = 1000
tone_duration = 2.0
fade_duration = 0.03
amp = 1.0

times = []

with open(labels_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if parts:
            try:
                times.append(float(parts[0]))
            except ValueError:
                pass

if not times:
    raise SystemExit("No label timestamps found.")

half_tone = tone_duration / 2
end_time = max(times) + half_tone + 1
total_samples = int(end_time * sample_rate)

audio = np.zeros(total_samples, dtype=np.float32)

tone_samples = int(tone_duration * sample_rate)
fade_samples = int(fade_duration * sample_rate)

t = np.arange(tone_samples) / sample_rate
tone = amp * np.sin(2 * np.pi * tone_freq * t)

# fade in/out
envelope = np.ones(tone_samples, dtype=np.float32)
envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

tone = tone * envelope

for ts in times:
    start = int((ts - half_tone) * sample_rate)
    tone_start = 0

    if start < 0:
        tone_start = -start
        start = 0

    end = min(start + tone_samples - tone_start, total_samples)
    n = end - start

    if n > 0:
        audio[start:end] += tone[tone_start:tone_start + n]

audio = np.clip(audio, -1.0, 1.0)
audio_int16 = (audio * 32767).astype(np.int16)

with wave.open(out_wav, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sample_rate)
    w.writeframes(audio_int16.tobytes())
