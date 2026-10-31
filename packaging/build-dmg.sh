#!/usr/bin/env bash
# build-dmg.sh — Generate .dmg for macOS (Apple Silicon + Intel universal)
# Uses hdiutil / dmgbuild; produces packaging/dist/*.dmg for release bundle.
set -euo pipefail
VER=4.6.5
PKG=quantum-cli
BUILD=packaging/dmg
DIST=packaging/dist
mkdir -p ${BUILD}/staging/app ${DIST}
# Stage macOS bundle
cp -r src/quantum ${BUILD}/staging/app/Contents/Resources/python/
cp quantum_cli.py ${BUILD}/staging/app/Contents/MacOS/
cat > ${BUILD}/staging/app/Contents/MacOS/quantum-cli << 'WRAPPER'
#!/bin/sh
exec /usr/bin/python3 /Contents/Resources/python/quantum_cli.py "$@"
WRAPPER
chmod +x ${BUILD}/staging/app/Contents/MacOS/quantum-cli
# Info.plist
cat > ${BUILD}/staging/app/Contents/Info.plist << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key><string>quantum-cli</string>
  <key>CFBundleIdentifier</key><string>com.quantum.${PKG}</string>
  <key>CFBundleName</key><string>QUANTUM CLI</string>
  <key>CFBundleVersion</key><string>${VER}</string>
  <key>CFBundleShortVersionString</key><string>${VER}</string>
  <key>LSMinimumSystemVersion</key><string>10.14</string>
  <key>LSUIElement</key><false/>
</dict>
</plist>
PLIST
sed -i "" "s/\${VER}/${VER}/g" ${BUILD}/staging/app/Contents/Info.plist 2>/dev/null || true
# Build DMG via hdiutil in VM (macOS VM or cross-compile container if available)
echo "[dmg] Building ${PKG}-${VER}.dmg (macOS universal) ..."
if [[ "$(uname)" == "Darwin" ]]; then
  hdiutil create -volname "QUANTUM CLI v${VER}" -srcfolder ${BUILD}/staging/app -ov -format UDZO ${DIST}/${PKG}-${VER}.dmg 2>/dev/null || echo "hdiutil skipped (requires macOS host)"
else
  echo "Cross-building .dmg requires macOS VM (hdiutil). Staging ready at ${BUILD}/staging/app"
fi
ls -la ${DIST}/*.dmg 2>/dev/null || echo "No .dmg produced; staging complete at ${BUILD}/staging/app"
