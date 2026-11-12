#!/bin/bash
# Package the patch for a release:  tools/package.sh VERSION  ->  dist/Ambient_Composer-VERSION.zip
set -e
cd "$(dirname "$0")/.."
VERSION="${1:-dev}"
rm -rf dist && mkdir -p dist/stage
cp -r "patches/Ambient Composer" dist/stage/
printf '0;\n' > "dist/stage/Ambient Composer/seed.txt"
printf 'Ambient Composer %s\n' "$VERSION" > "dist/stage/Ambient Composer/VERSION.txt"
(cd dist/stage && zip -qr "../Ambient_Composer-${VERSION}.zip" .)
rm -rf dist/stage
ls -l dist
