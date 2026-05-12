#!/bin/bash

# Test that concurrent setup_rust calls don't race on rustup-init download.
# https://github.com/rust-lang/rustup/issues/4607

set -euo pipefail

docker build -f parallelism.dockerfile -t puccinialin-parallelism ..

docker run --rm -i puccinialin-parallelism /bin/bash -c '
  set -uo pipefail
  for _ in $(seq 1 4); do
    uv run python -c "from puccinialin import setup_rust; setup_rust(\"foo\")" &
  done
  wait
' 2>&1 | tee /tmp/puccinialin-parallel-output.log

downloads=$(grep -c "^Downloading rustup-init from" /tmp/puccinialin-parallel-output.log || true)
if [ "$downloads" -gt 1 ]; then
  echo "FAIL: rustup-init downloaded $downloads times (expected 1)."
  exit 1
fi
