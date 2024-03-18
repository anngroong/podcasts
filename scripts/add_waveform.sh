#!/bin/bash

video_filename="${1:-video.mp4}"
output_filename="${2:-output.mp4}"
vertical_offset_percent=40

# Check if the video file exists
if [ ! -f "$video_filename" ]; then
    echo "Error: File '$video_filename' doesn't exist."
    exit 1
fi

image_x=$(ffprobe -v quiet -print_format json -show_format -show_streams $video_filename|jq '.streams[] | select(.codec_type == "video") | .width')
image_y=$(ffprobe -v quiet -print_format json -show_format -show_streams $video_filename|jq '.streams[] | select(.codec_type == "video") | .height')

wave_height=$(( $image_y * $vertical_offset_percent / 100 ))

# -filter_complex "[0:v]showwaves=s=${image_x}x${image_y}:scale=sqrt:colors=0xfbfbfb@0.3:mode=cline,format=yuva420p[v];[v]scale=${image_x}:${wave_height}[v];[1:v][v]overlay=(W-w)/2:H-h[outv]" \

# -filter_complex "[0:a]showwaves=s=1280x720:mode=line:colors=white[wave];[0:v][wave]overlay=0:H-h" -c:v libx264 -c:a copy output.mp4

ffmpeg \
-i $video_filename \
-filter_complex "[0:a]showwaves=s=${image_x}x${image_y}:scale=sqrt:colors=0xfbfbfb@0.3:mode=cline,format=yuva420p[v];[v]scale=${image_x}:${wave_height}[v];[0:v][v]overlay=(W-w)/2:H-h" \
-c:v libx264 -c:a copy \
-preset ultrafast \
$output_filename
