#!/usr/bin/env python3
import sys, wave, math, struct

labels_file = sys.argv[1]
out_wav = sys.argv[2]

sample_rate = 48000
tone_freq = 707
tone_duration = 1.0
fade_duration = 0.03   # 30 ms fade
amp = 1.0

times = []

with open(labels_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) >= 1:
            try:
                times.append(float(parts[0]))
            except ValueError:
                pass

if not times:
    raise SystemExit("No label timestamps found.")

half_tone = tone_duration / 2
end_time = max(times) + half_tone + 1

total_samples = int(end_time * sample_rate)
audio = [0.0] * total_samples

tone_samples = int(tone_duration * sample_rate)
fade_samples = int(fade_duration * sample_rate)

for t in times:
    start_time = max(0, t - half_tone)
    start = int(start_time * sample_rate)

    for i in range(tone_samples):
        idx = start + i
        if idx >= total_samples:
            break

        # fade envelope
        if i < fade_samples:
            envelope = i / fade_samples
        elif i > tone_samples - fade_samples:
            envelope = (tone_samples - i) / fade_samples
        else:
            envelope = 1.0

        sample = amp * envelope * math.sin(
            2 * math.pi * tone_freq * i / sample_rate
        )

        audio[idx] += sample

with wave.open(out_wav, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sample_rate)

    for s in audio:
        s = max(-1.0, min(1.0, s))
        w.writeframes(struct.pack("<h", int(s * 32767)))
