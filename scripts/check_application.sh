#!/bin/sh
set -eu
python3 -m compileall -q rapbattle tests
node --check rapbattle/engine_bridge.mjs
python3 -m unittest discover -s tests -v
