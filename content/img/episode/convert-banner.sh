#!/bin/bash

if [ ! -f $1 ]
then
  echo "File __$1__ is missing"
fi

webpfile="${1%.png}.webp"

convert $1 $webpfile
