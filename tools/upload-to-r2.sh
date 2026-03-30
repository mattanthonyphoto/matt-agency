#!/bin/bash
# Upload site images to Cloudflare R2
#
# Prerequisites:
#   1. Install wrangler: npm install -g wrangler
#   2. Login: wrangler login
#   3. Create R2 bucket: wrangler r2 bucket create mattanthonyphoto-images
#
# Usage:
#   bash tools/upload-to-r2.sh                    # Upload all images
#   bash tools/upload-to-r2.sh --dry-run          # Preview what would upload

set -e

BUCKET="mattanthonyphoto-images"
IMAGE_DIR=".tmp/site-images"
DRY_RUN=false

if [ "$1" = "--dry-run" ]; then
  DRY_RUN=true
fi

if [ ! -d "$IMAGE_DIR" ]; then
  echo "Error: Image directory not found at $IMAGE_DIR"
  echo "Run 'python tools/download-site-images.py --download' first"
  exit 1
fi

COUNT=$(find "$IMAGE_DIR" -type f | wc -l | tr -d ' ')
echo "Found $COUNT images to upload to R2 bucket: $BUCKET"

if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "DRY RUN — would upload these files:"
  find "$IMAGE_DIR" -type f -name "*.jpg" -o -name "*.png" -o -name "*.webp" | head -20
  echo "... and $(( COUNT - 20 )) more"
  echo ""
  echo "Total size: $(du -sh "$IMAGE_DIR" | cut -f1)"
  echo ""
  echo "Run without --dry-run to upload"
  exit 0
fi

echo ""
UPLOADED=0
FAILED=0

for file in "$IMAGE_DIR"/*; do
  if [ -f "$file" ]; then
    filename=$(basename "$file")

    # Set content type based on extension
    case "$filename" in
      *.jpg|*.jpeg) CONTENT_TYPE="image/jpeg" ;;
      *.png) CONTENT_TYPE="image/png" ;;
      *.webp) CONTENT_TYPE="image/webp" ;;
      *.svg) CONTENT_TYPE="image/svg+xml" ;;
      *) CONTENT_TYPE="application/octet-stream" ;;
    esac

    if wrangler r2 object put "$BUCKET/$filename" \
      --file="$file" \
      --content-type="$CONTENT_TYPE" \
      --cache-control="public, max-age=31536000, immutable" \
      --remote \
      2>/dev/null; then
      UPLOADED=$((UPLOADED + 1))
      echo "  [$UPLOADED/$COUNT] $filename"
    else
      FAILED=$((FAILED + 1))
      echo "  FAILED: $filename"
    fi
  fi
done

echo ""
echo "Done!"
echo "  Uploaded: $UPLOADED"
echo "  Failed: $FAILED"
echo ""
echo "Next steps:"
echo "  1. Set up custom domain in Cloudflare dashboard:"
echo "     R2 > mattanthonyphoto-images > Settings > Custom Domains"
echo "     Add: images.mattanthonyphoto.com"
echo "  2. Rebuild site with image base URL:"
echo "     python tools/build-site.py --image-base https://images.mattanthonyphoto.com"
