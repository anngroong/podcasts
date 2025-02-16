#!/bin/bash

# Truncate a video file and get the first portion of it
# based on specified timestamp.
#
# Usage: clip-video.sh <filename> <mm:ss> (by default 1min)
#
# The above will get the first mm:ss of the video and output
# it to a new file called <filename_clipped>

video_file="${1:-video.mp4}"
end_timestamp="${2:-1:00}"

# Check if the video file exists
if [ ! -f "$video_file" ]; then
    echo "Error: File '$video_file' doesn't exist."
    exit 1
fi

# Regular expressions for mm:ss and hh:mm:ss
pattern_mm_ss='^[0-5]?[0-9]:[0-5][0-9]$'
pattern_hh_mm_ss='^[0-9]+:[0-5][0-9]:[0-5][0-9]$'

if [[ "$end_timestamp" =~ $pattern_mm_ss ]]; then
    # Valid mm:ss format for end_timestamp
    :
elif [[ "$end_timestamp" =~ $pattern_hh_mm_ss ]]; then
    # Valid hh:mm:ss format for end_timestamp
    :
else
    echo "Invalid time format: $end_timestamp"
    exit
fi

output_filename="${video_file%%.*}_clipped.mp4"

ffmpeg -i $video_file -to $end_timestamp $output_filename
