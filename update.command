#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Frontend bauen ==="
cd apps/web
npx next build
cd ../..

echo "=== Desktop bauen ==="
cd apps/desktop
rm -rf web-out
cp -r ../web/out web-out
npx electron-builder --mac

APP_SRC="release/mac-arm64/Sagent.app"
APP_DST="/Applications/Sagent.app"

if [ -d "$APP_DST" ]; then
  echo "=== App in /Applications ersetzen ==="
  rm -rf "$APP_DST"
fi
cp -R "$APP_SRC" "$APP_DST"
echo ""
echo "=== Fertig! Sagent wurde in /Applications aktualisiert ==="
echo "Starte es neu aus dem Programme-Ordner."
