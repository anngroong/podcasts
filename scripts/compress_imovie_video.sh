#!/bin/bash

input_file="${1:-input.mp4}"
output_file="${2:-output.mp4}"

# Check if the input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: File '$input_file' doesn't exist."
    exit 1
fi

ffmpeg -i $input_file -vcodec libx264 -crf 23 -preset slow -movflags +faststart $output_file

