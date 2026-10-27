#!/bin/bash
# frames + mixed audio + burned-in English subtitles -> videos/<ep>.mp4
set -e
cd "$(dirname "$0")"
ep=$1
B=build/$ep
name=$(python3 -c "import sys; sys.path.insert(0,'episodes'); import ${ep}_story as s; print((s.TITLE+' - '+s.SUBTITLE).replace(':','').replace('&','and').replace(' ','_'))")
mkdir -p videos
ffmpeg -y -hide_banner -loglevel error -framerate 24 -i "$B/frames/%04d.png" -i "$B/mix.wav" \
  -vf "scale=1080:1920:flags=lanczos,subtitles=$B/subs.ass" \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart \
  "videos/${ep}_${name}.mp4"
echo "videos/${ep}_${name}.mp4"
