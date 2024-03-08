#!/bin/bash

# Generate an audio by combining 3 input audio files.
# Apply crossfade in between.

intro_filename="${1:-intro.wav}"
audio_filename="${2:-input.wav}"
outro_filename="${3:-outro.wav}"
output_filename="${4:-output.wav}"

# Check if the files exist
if [ ! -f "$intro_filename" ]; then
    echo "Error: File '$intro_filename' doesn't exist."
    exit 1
fi
if [ ! -f "$audio_filename" ]; then
    echo "Error: File '$audio_filename' doesn't exist."
    exit 1
fi
if [ ! -f "$outro_filename" ]; then
    echo "Error: File '$outro_filename' doesn't exist."
    exit 1
fi
if [ -f "$output_filename" ]; then
    echo "Error: OUTPUT File '$output_filename' exists, refusing to overwrite."
    exit 1
fi

ffmpeg -i $intro_filename -i $audio_filename -i $outro_filename \
	-filter_complex "[0][1]acrossfade=d=1:c1=tri:c2=tri[a01]; [a01][2]acrossfade=d=1:c1=tri:c2=tri;" \
	$output_filename
