#!/bin/bash

# This script expects to be run from the root of the repository.
# Converts all thumbnail-NNN.png files to thumbnail-NNN.jpg files.
# It also edits the episode markdown file in place to change the reference in the file.

modify_file () {
  bn=$( basename $1 )
  ep=$( echo $bn | sed -r 's/thumbnail-([0-9]*)\.png/\1/g' )
  jpgfile="${bn%.png}.jpg"
  for f in `find content/episode -name ${ep}-*.md`
  do
     echo "	Modifying $f"
     gsed -i s/${bn}/${jpgfile}/g ${f}
  done
}

for i in `find content/img/episode -name thumbnail-*.png`
do
    output="${i%.png}.jpg"
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
    modify_file $i 
done
 
