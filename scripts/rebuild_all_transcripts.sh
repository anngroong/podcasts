#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-.}"
cd "$REPO_ROOT"

TRANSCRIPTS_DIR="transcripts"
SCRIPT="scripts/substack_to_hugo_transcript.py"

if [[ ! -d "$TRANSCRIPTS_DIR" ]]; then
  echo "Error: transcripts directory not found: $TRANSCRIPTS_DIR" >&2
  exit 1
fi

if [[ ! -f "$SCRIPT" ]]; then
  echo "Error: transcript generator not found: $SCRIPT" >&2
  exit 1
fi

SHOW_IDS=()
while IFS= read -r line; do
  SHOW_IDS+=("$line")
done < <(
  find "$TRANSCRIPTS_DIR" -maxdepth 1 -type f -name '*.txt' \
    | sed -E 's|.*/||' \
    | sed -nE 's/^([0-9]+)-.*\.txt$/\1/p' \
    | sort -n -u
)

if [[ ${#SHOW_IDS[@]} -eq 0 ]]; then
  echo "No transcript files found in $TRANSCRIPTS_DIR" >&2
  exit 0
fi

echo "Found ${#SHOW_IDS[@]} show(s) to process."

FAILED=0

for SHOW_ID in "${SHOW_IDS[@]}"; do
  echo "Processing show $SHOW_ID..."
  if ! python3 "$SCRIPT" "$SHOW_ID"; then
    echo "Failed: show $SHOW_ID" >&2
    FAILED=1
  fi
done

if [[ $FAILED -ne 0 ]]; then
  echo "Finished with one or more failures." >&2
  exit 1
fi

echo "Done."
