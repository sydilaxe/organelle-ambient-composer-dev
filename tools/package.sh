#!/bin/bash
# Package the patch for a release:  tools/package.sh VERSION
#   -> dist/Amble-VERSION.zip (the patch folder, with the manual inside) and dist/Amble-manual-VERSION.pdf
set -e
cd "$(dirname "$0")/.."
VERSION="${1:-dev}"
rm -rf dist && mkdir -p dist/stage
cp -r "patches/Amble" dist/stage/
printf '0;\n' > "dist/stage/Amble/seed.txt"
rm -f "dist/stage/Amble/saves.txt"      # your saves stay when you copy a new version over the old one
printf 'Amble %s\n' "$VERSION" > "dist/stage/Amble/VERSION.txt"
# the manual, generated from the same source as the patch (fails if a control has no description)
python3 tools/manual.py "$VERSION" "dist/Amble-manual-${VERSION}.pdf"
cp "dist/Amble-manual-${VERSION}.pdf" "dist/stage/Amble/Amble-manual.pdf"
(cd dist/stage && zip -qr "../Amble-${VERSION}.zip" .)
rm -rf dist/stage
ls -l dist
