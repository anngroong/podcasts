#!/bin/bash

image_filename="${1:-title.jpg}"
audio_filename="${2:-full_show_mixed.wav}"
output_filename="${3:-output.mov}"

# Check if the image file exists
if [ ! -f "$image_filename" ]; then
    echo "Error: File '$image_filename' doesn't exist."
    exit 1
fi

# Check if the audio file exists
if [ ! -f "$audio_filename" ]; then
    echo "Error: File '$audio_filename' doesn't exist."
    exit 1
fi

image_x=$(identify -format "%w" $image_filename)
image_y=$(identify -format "%h" $image_filename)

# ffmpeg -loop 0 -i $audio_filename -i $image_filename -c:v libx264 -tune stillimage -shortest -pix_fmt yuv420p -preset ultrafast $output_filename

wave_height=$(( $image_y / 3 ))

ffmpeg \
-i $audio_filename \
-i $image_filename \
-filter_complex "[0:a]showwaves=s=${image_x}x${image_y}:scale=sqrt:colors=0xfbfbfb@0.3:mode=cline,format=yuva420p[v];[v]scale=${image_x}:${wave_height}[v];[1:v][v]overlay=(W-w)/2:H-h[outv]" \
-map "[outv]" -pix_fmt yuv420p -map 0:a \
-c:v libx264 \
-preset ultrafast \
$output_filename
