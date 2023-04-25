#!/bin/bash

if [ ! -f $1 ]
then
  echo "File __$1__ is missing"
fi

webpfile="${1%.png}.webp"

convert -quality 25 -resize 1400x1400 $1 $webpfile
