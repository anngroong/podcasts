#!/bin/bash

# This script expects to be run from the root of the repository.
# Converts all thumbnail-NNN.png files to thumbnail-NNN.webp files.
# It also edits the episode markdown file in place to change the reference in the file.

modify () {
  bn=$( basename $1 )
  ep=$( echo $bn | sed -r 's/^[a-z]+-([0-9]*)\.png/\1/g' )
  webpfile="${bn%.png}.webp"
  echo "for f in find content/episode -name ${ep}-*.md"
  for f in `find content/episode -name ${ep}-*.md`
  do
     echo "	Modifying $f for $bn"
     gsed -i s/${bn}/${webpfile}/g ${f}
  done
}

# PROCESS THUMBNAILS
for i in `find content/img/episode -name thumbnail-*.png|sort`
do
    output="${i%.png}.webp"
    # Comment out the following IF statement to run across all episodes.
    if [ -f "$output" ]; then
       # Skipping for existing files
       echo $output exists, skipping.
       continue
    fi

    echo WORKING on $i
    convert -quality 25 -resize 1400x1400 $i $output 2>/dev/null
    ORIG_FILESIZE=$(stat -f%z "$i")
    DEST_FILESIZE=$(stat -f%z "$output")
    REDUCTION=$( printf %.2f $( echo "(1 - $DEST_FILESIZE/$ORIG_FILESIZE) * 100" | bc -l ) )
    echo "INPUT: $i ORIG: $ORIG_FILESIZE DEST: $DEST_FILESIZE REDUCTION: ${REDUCTION}%"
    modify $i
done

# PROCESS BANNERS
for i in `find content/img/episode -name banner-*.png|sort`
do
    output="${i%.png}.webp"
    # Comment out the following IF statement to run across all episodes.
    # if [ -f "$output" ]; then
    #    # Skipping for existing files
    #    echo $output exists, skipping.
    #    continue
    # fi

    echo WORKING on $i
    convert $i $output 2>/dev/null
    ORIG_FILESIZE=$(stat -f%z "$i")
    DEST_FILESIZE=$(stat -f%z "$output")
    REDUCTION=$( printf %.2f $( echo "(1 - $DEST_FILESIZE/$ORIG_FILESIZE) * 100" | bc -l ) )
    echo "INPUT: $i ORIG: $ORIG_FILESIZE DEST: $DEST_FILESIZE REDUCTION: ${REDUCTION}%"
    modify $i
done
