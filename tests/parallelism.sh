#!/bin/bash

# Test that running in parallel doesn't fail
# https://github.com/rust-lang/rustup/issues/4607

docker build -f parallelism.dockerfile -t puccinialin-parallelism ..

docker run --rm -i puccinialin-parallelism /bin/bash -c "
  uv run python -c 'from puccinialin import setup_rust; setup_rust(\"foo\")' & \
  uv run python -c 'from puccinialin import setup_rust; setup_rust(\"foo\")' & \
  uv run python -c 'from puccinialin import setup_rust; setup_rust(\"foo\")' & \
  wait -n
"