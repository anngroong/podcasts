#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="groong-cloud"
REGION="us-central1"
REPO="groong-docker-repo"
IMAGE_NAME="groong-scraper"
TAG="latest"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:${TAG}"

docker run --rm -v "$(pwd)":/out "${IMAGE_URI}" "$@"

