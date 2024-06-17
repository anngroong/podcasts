#!/bin/bash

FONT="/System/Library/Fonts/Supplemental/Microsoft Sans Serif.ttf"

input_filename="${1:-input.mp4}"
subtitle_text="${2:-GROONG}"
output_filename="${3:-output.mp4}"

# Check if the input file exists
if [ ! -f "$input_filename" ]; then
    echo "Error: File '$input_filename' doesn't exist."
    exit 1
fi

text_x=10
text_y="h-th-10"


ffmpeg -i $input_filename \
	-vf "drawtext=fontfile=${FONT}:text=\'$subtitle_text\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=$text_x:y=$text_y" \
	-codec:a copy $output_filename
