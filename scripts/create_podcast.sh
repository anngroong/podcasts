#!/bin/bash
set -euo pipefail

usage() {
  cat <<EOF
Usage:
  $(basename "$0") [--no-waveform|-n] [--waveform|-w] [image] [audio] [output]

Defaults:
  image  = title.jpg
  audio  = full_show_mixed.wav
  output = output.mov
  waveform = ON (same as before)

Examples:
  $(basename "$0")
  $(basename "$0") title.jpg full_show_mixed.wav output.mov
  $(basename "$0") --no-waveform title.jpg full_show_mixed.wav output.mov
EOF
}

waveform=1

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--no-waveform) waveform=0; shift ;;
    -w|--waveform)    waveform=1; shift ;;
    -h|--help)        usage; exit 0 ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; usage; exit 2 ;;
    *)  break ;;
  esac
done

image_filename="${1:-title.jpg}"
audio_filename="${2:-full_show_mixed.wav}"
output_filename="${3:-output.mov}"

# Check inputs
if [ ! -f "$image_filename" ]; then
  echo "Error: File '$image_filename' doesn't exist." >&2
  exit 1
fi

if [ ! -f "$audio_filename" ]; then
  echo "Error: File '$audio_filename' doesn't exist." >&2
  exit 1
fi

image_x=$(identify -format "%w" "$image_filename")
image_y=$(identify -format "%h" "$image_filename")
wave_height=$(( image_y / 3 ))

if [[ "$waveform" -eq 1 ]]; then
  # Waveform ON (original behavior), but with image loop + shortest for robustness
  ffmpeg \
    -i "$audio_filename" \
    -loop 1 -i "$image_filename" \
    -filter_complex "[0:a]showwaves=s=${image_x}x${image_y}:scale=sqrt:colors=0xfbfbfb@0.3:mode=cline,format=yuva420p[w];[w]scale=${image_x}:${wave_height}[w];[1:v][w]overlay=(W-w)/2:H-h[outv]" \
    -map "[outv]" -map 0:a \
    -c:v libx264 -tune stillimage -pix_fmt yuv420p \
    -preset ultrafast \
    -shortest \
    "$output_filename"
else
  # Waveform OFF (simple still image video + audio)
  ffmpeg \
    -i "$audio_filename" \
    -loop 1 -i "$image_filename" \
    -map 1:v -map 0:a \
    -c:v libx264 -tune stillimage -pix_fmt yuv420p \
    -preset ultrafast \
    -shortest \
    "$output_filename"
fi
