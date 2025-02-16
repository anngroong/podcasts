#!/bin/bash

# Given the PNG version of banner file and thumbnail file, convert each of them to 
# JPG and WEBP format, which is a common operation in publishing a podcast.

episode_number="${1:-99999.png}"

banner_file="banner-${episode_number}.png"
thumbnail_file="thumbnail-${episode_number}.png"

# Check if the banner file exists
if [ ! -f "$banner_file" ]; then
    echo "Error: File '$banner_file' doesn't exist."
    exit 1
fi

# Check if the thumbnail file exists
if [ ! -f "$thumbnail_file" ]; then
    echo "Error: File '$thumbnail_file' doesn't exist."
    exit 1
fi

banner_jpg="banner-${episode_number}.jpg"
banner_webp="banner-${episode_number}.webp"
thumbnail_jpg="thumbnail-${episode_number}.jpg"
thumbnail_webp="thumbnail-${episode_number}.webp"

convert -quality 50 -resize 1280x720 $banner_file $banner_jpg
convert -quality 50 -resize 1280x720 $banner_file $banner_webp
convert -quality 50 -resize 1500x1500 $thumbnail_file $thumbnail_jpg
convert -quality 50 -resize 1500x1500 $thumbnail_file $thumbnail_webp
