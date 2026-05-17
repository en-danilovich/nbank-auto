#!/usr/bin/env bash
set -euo pipefail

# Configurable via environment variables:
#   DOCKERHUB_USERNAME  - your Docker Hub username (required)
#   DOCKERHUB_TOKEN     - Docker Hub access token (required; never commit it)
#   LOCAL_IMAGE         - source image already built locally (default: python-tests:first-dockerfile)
#   IMAGE_NAME          - target repo name on Docker Hub (default: nbank-tests)
#   TAG                 - target tag (default: latest)

LOCAL_IMAGE="${LOCAL_IMAGE:-python-tests:first-dockerfile}"
IMAGE_NAME="${IMAGE_NAME:-nbank-tests}"
TAG="${TAG:-latest}"

if [[ -z "${DOCKERHUB_USERNAME:-}" ]]; then
  echo "ERROR: DOCKERHUB_USERNAME is not set" >&2
  exit 1
fi

if [[ -z "${DOCKERHUB_TOKEN:-}" ]]; then
  echo "ERROR: DOCKERHUB_TOKEN is not set (export it or load from .env)" >&2
  exit 1
fi

REMOTE_IMAGE="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${TAG}"

echo "==> Logging in to Docker Hub as ${DOCKERHUB_USERNAME}"
echo "${DOCKERHUB_TOKEN}" | docker login --username "${DOCKERHUB_USERNAME}" --password-stdin

echo "==> Tagging ${LOCAL_IMAGE} -> ${REMOTE_IMAGE}"
docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"

echo "==> Pushing ${REMOTE_IMAGE}"
docker push "${REMOTE_IMAGE}"

echo ""
echo "Done. Pull it anywhere with:"
echo "  docker pull ${REMOTE_IMAGE}"
