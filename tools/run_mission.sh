#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f maps/slam_provenance.json ]]; then
  echo 'Run bash tools/run_slam.sh first to produce and record a real SLAM map.' >&2
  exit 1
fi
docker-compose up
