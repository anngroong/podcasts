#!/bin/bash

input_file="${1:-input.mp4}"

# If output file is provided, insert _small before extension
if [ -n "$2" ]; then
    output_file="${2%.*}_small.${2##*.}"
else
    # Otherwise derive from input file
    output_file="${input_file%.*}_small.${input_file##*.}"
fi

# Check if the input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: File '$input_file' doesn't exist."
    exit 1
fi

ffmpeg -i "$input_file" -vcodec libx264 -crf 23 -preset slow -movflags +faststart "$output_file"
