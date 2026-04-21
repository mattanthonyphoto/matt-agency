#!/usr/bin/env bash
# Batch-render all 21 LRD story compositions, compress, and deploy
# to the client-portal public/stories/ folders.
set -euo pipefail

cd "$(dirname "$0")/.."

RAW_DIR="output/lrd-stories-raw"
COMP_DIR="output/lrd-stories-compressed"
PORTAL_DIR="../client-portal/public/stories"

mkdir -p "$RAW_DIR" "$COMP_DIR"

# composition-id  portal-subfolder
compositions=(
  "LRD-Story-Sunstone-Award sunstone"
  "LRD-Story-Sunstone-Kitchen sunstone"
  "LRD-Story-Sunstone-Details sunstone"
  "LRD-Story-Sunstone-Primary sunstone"
  "LRD-Story-Sunstone-Mountain sunstone"
  "LRD-Story-Tapleys-Transformation tapleys"
  "LRD-Story-Tapleys-Kitchen tapleys"
  "LRD-Story-Tapleys-Craft tapleys"
  "LRD-Story-Tapleys-Generations tapleys"
  "LRD-Story-Sunridge-Tower sunridge"
  "LRD-Story-Sunridge-Heritage sunridge"
  "LRD-Story-Sunridge-Kitchen sunridge"
  "LRD-Story-Sunridge-Bathrooms sunridge"
  "LRD-Story-Sunridge-Artists sunridge"
  "LRD-Story-Balsam-Kitchen balsam"
  "LRD-Story-Balsam-WineRoom balsam"
  "LRD-Story-Balsam-Details balsam"
  "LRD-Story-Balsam-Stone balsam"
  "LRD-Story-SRAM-Space sram"
  "LRD-Story-SRAM-Brand sram"
  "LRD-Story-SRAM-WorkLife sram"
)

for entry in "${compositions[@]}"; do
  comp_id=$(echo "$entry" | awk '{print $1}')
  project=$(echo "$entry" | awk '{print $2}')

  raw_path="$RAW_DIR/${comp_id}.mp4"
  comp_path="$COMP_DIR/${comp_id}.mp4"
  portal_path="$PORTAL_DIR/$project/${comp_id}.mp4"

  echo ""
  echo "=== Rendering $comp_id ==="
  npx remotion render src/index.tsx "$comp_id" "$raw_path" \
    --codec h264 --crf 21 --log=warn

  echo "=== Compressing $comp_id ==="
  # Instagram Stories reject yuvj420p (full-range JPEG) and High-profile
  # H.264. Remotion's raw output is yuvj420p, so the -vf scale filter is
  # required to actually convert the range — just setting -pix_fmt isn't
  # enough when the source is already JPEG-range. Seen on Apr 21: stories
  # got "Instagram media processing failed" until this filter was added.
  ffmpeg -y -loglevel error -i "$raw_path" \
    -vf "scale=in_range=pc:out_range=tv,format=yuv420p" \
    -c:v libx264 -crf 26 -preset medium \
    -profile:v main -level 4.0 \
    -movflags +faststart \
    -c:a aac -b:a 128k -ar 48000 \
    "$comp_path"

  echo "=== Deploying to $portal_path ==="
  mkdir -p "$(dirname "$portal_path")"
  cp "$comp_path" "$portal_path"

  ls -la "$portal_path"
done

echo ""
echo "=== Done. Total portal stories size: ==="
du -sh "$PORTAL_DIR"
