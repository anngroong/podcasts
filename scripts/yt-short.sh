#!/bin/bash

# Truncate a video file to the first 60 seconds and make it into 
# a square aspect ratio, for Youtube shorts.
#
# Usage: yt-short.sh <filename>
#

video_file="${1:-video.mp4}"
length="${2:-1080}"

# Check if the video file exists
if [ ! -f "$video_file" ]; then
    echo "Error: File '$video_file' doesn't exist."
    exit 1
fi

output_filename="${video_file%.*}_ytshort.mp4"

ffmpeg -i "$1" \
        -to 3:00 -c:v libx264 -crf 23 \
        -filter_complex "[0:v]split=2[blur][vid];[blur]scale=${length}:${length}:force_original_aspect_ratio=increase,crop=${length}:${length},boxblur=luma_radius=min(h\,w)/20:luma_power=1:chroma_radius=min(cw\,ch)/20:chroma_power=1[bg];[vid]scale=${length}:${length}:force_original_aspect_ratio=decrease[ov];[bg][ov]overlay=(W-w)/2:(H-h)/2" \
        -profile:v baseline -level 3.0 -pix_fmt yuv420p -preset faster -tune fastdecode \
        -c:a aac -ac 2 -b:a 128k -movflags faststart "$output_filename"
