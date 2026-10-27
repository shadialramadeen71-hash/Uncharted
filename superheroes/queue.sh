#!/bin/bash
# render episodes one after another (resumable: finished frames are skipped)
cd "$(dirname "$0")"
for ep in "$@"; do
  python3 render.py "$ep" > "build/$ep/render.log" 2>&1
  ./make_video.sh "$ep" >> "build/$ep/render.log" 2>&1
done
