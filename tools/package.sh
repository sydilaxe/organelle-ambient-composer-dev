#!/bin/bash
# Package the patch for a release:  tools/package.sh VERSION  ->  dist/Amble-VERSION.zip
set -e
cd "$(dirname "$0")/.."
VERSION="${1:-dev}"
rm -rf dist && mkdir -p dist/stage
cp -r "patches/Amble" dist/stage/
printf '0;\n' > "dist/stage/Amble/seed.txt"
printf 'Amble %s\n' "$VERSION" > "dist/stage/Amble/VERSION.txt"
(cd dist/stage && zip -qr "../Amble-${VERSION}.zip" .)
rm -rf dist/stage
ls -l dist
