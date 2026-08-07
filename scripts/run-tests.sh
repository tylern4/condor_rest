#!/usr/bin/env bash
set -euo pipefail

# Run the condor_rest test suite inside a Linux container.
#
# The `htcondor` package only ships Linux wheels, so the suite cannot run
# natively on macOS. This script builds a small image with dependencies
# pre-installed (Docker layer caching keeps rebuilds fast) and runs pytest
# inside it. Extra arguments are passed through to pytest, e.g.:
#
#   scripts/run-tests.sh                  # full suite
#   scripts/run-tests.sh -k submit        # only tests matching "submit"
#   scripts/run-tests.sh tests/test_auth.py
#
# Overridable via environment:
#   TEST_IMAGE       image tag to use (default: htcondor-rest-tests)
#   TEST_DOCKERFILE  path to the Dockerfile (default: Dockerfile.test)
#   TEST_PYTHON_TAG  base python image tag (default: 3.13-slim)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${TEST_IMAGE:-htcondor-rest-tests}"
DOCKERFILE="${TEST_DOCKERFILE:-$REPO_ROOT/Dockerfile.test}"
PYTHON_TAG="${TEST_PYTHON_TAG:-3.13-slim}"

cd "$REPO_ROOT"

echo "Building test image ${IMAGE} (cached across runs)..." >&2
docker build \
    --build-arg PYTHON_TAG="$PYTHON_TAG" \
    -f "$DOCKERFILE" \
    -t "$IMAGE" \
    .

echo "Running pytest inside ${IMAGE}..." >&2
exec docker run \
    --rm \
    -v "$HOME/.cache/uv:/root/.cache/uv" \
    "$IMAGE" \
    uv run pytest "$@"
