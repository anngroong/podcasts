#!/bin/bash

# Given a text file (speech.txt) generate an mp3 of the speech.
# Requires gcloud to be installed and initialized/authenticated.

TMPFILE1=$(mktemp)
TMPFILE2=$(mktemp)

speech_filename="${1:-speech.txt}"
output_filename="${2:-output-voice.mp3}"

# Check if the files exist
if [ ! -f "$speech_filename" ]; then
    echo "Error: Speech file '$speech_filename' doesn't exist."
    exit 1
fi

IFS='' read -r -d '' TEMPLATE <<'EOF'
{
  "input": {
    "text": ""
  },
  "voice": {
    "languageCode": "en-US",
    "name": "en-US-Journey-F",
    "ssmlGender": "FEMALE"
  },
  "audioConfig": {
    "audioEncoding": "MP3"
  }
}
EOF

echo $TEMPLATE > $TMPFILE1

# https://cloud.google.com/text-to-speech/docs/create-audio-text-command-line

speech=$(cat ${speech_filename}|tr -d "\""|tr -d "'")

mycmd="jq '.input.text = \"${speech}\"' $TMPFILE1 > $TMPFILE2"

eval "$mycmd"

curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: groong" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d @${TMPFILE2} \
    "https://texttospeech.googleapis.com/v1/text:synthesize" 2>/dev/null | jq ".audioContent" |sed -e 's/^"//'|sed -e 's/"$//'|	base64 -d > $output_filename
