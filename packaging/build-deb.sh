#!/usr/bin/env bash
# build-deb.sh — Generate .deb package for QUANTUM-CLI (Debian/Ubuntu/Kali)
# Runs in a clean VM/container; produces packaging/dist/*.deb for next release.
set -euo pipefail
PKG=quantum-cli
VER=$(python -c "import sys; print(open('src/quantum/version.py').read().split('=')[1].strip() if __import__('os').path.exists('src/quantum/version.py') else '4.6.5')" 2>/dev/null || echo "4.6.5")
ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")
BUILD=packaging/deb
mkdir -p ${BUILD}/${PKG}-${VER}/DEBIAN ${BUILD}/${PKG}-${VER}/usr/bin ${BUILD}/${PKG}-${VER}/usr/lib/${PKG} ${BUILD}/${PKG}-${VER}/usr/share/applications
# Copy package source and CLI entry point
cp -r src/quantum ${BUILD}/${PKG}-${VER}/usr/lib/${PKG}/python
cp quantum_cli.py ${BUILD}/${PKG}-${VER}/usr/lib/${PKG}/
# Executable wrapper
cat > ${BUILD}/${PKG}-${VER}/usr/bin/quantum-cli << 'WRAPPER'
#!/bin/sh
exec /usr/bin/python3 /usr/lib/quantum-cli/quantum_cli.py "$@"
WRAPPER
chmod +x ${BUILD}/${PKG}-${VER}/usr/bin/quantum-cli
# Desktop entry
cat > ${BUILD}/${PKG}-${VER}/usr/share/applications/quantum-cli.desktop << 'DESK'
[Desktop Entry]
Name=QUANTUM CLI
Comment=Authorized penetration-test framework (v${VER})
Exec=quantum-cli
Type=Application
Terminal=true
Icon=quantum-cli
Categories=Security;System;
DESK
sed -i "s/v\${VER}/${VER}/g" ${BUILD}/${PKG}-${VER}/usr/share/applications/quantum-cli.desktop || true
# Control file
cat > ${BUILD}/${PKG}-${VER}/DEBIAN/control << CTRL
Package: quantum-cli
Version: ${VER}
Section: security
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>=3.9), flask, requests, waitress, pycryptodome, impacket, pysmb, colorama
Maintainer: Project Zero <projectzero@quantum.local>
Description: QUANTUM CLI — Authorized C2 / penetration framework
 Authorized engagements only. Real modules, real exploits,
 zero simulated behavior. Includes autonomous factory (/auto),
 God Mode agent (/god), and 175 executable RAT/C2 modules.
CTRL
# Install and build in VM (Docker/VM path for isolation)
echo "[deb] Building ${PKG}_${VER}_${ARCH}.deb inside VM/docker..."
mkdir -p packaging/dist
if command -v docker >/dev/null 2>&1; then
  docker run --rm -v "$(pwd):/work" -w /work debian:bookworm bash -c "
    apt update -qq && apt install -y -qq dpkg-dev >/dev/null 2>&1 || true
    dpkg-deb --build packaging/deb/quantum-cli-${VER} packaging/dist/quantum-cli_${VER}_${ARCH}.deb
  " || echo "Docker VM skipped; build manually with: dpkg-deb --build packaging/deb/quantum-cli-${VER}"
else
  dpkg-deb --build ${BUILD}/${PKG}-${VER} packaging/dist/${PKG}_${VER}_${ARCH}.deb || echo "VM build skipped; package prepared at ${BUILD}/${PKG}-${VER}"
fi
ls -la packaging/dist/*.deb 2>/dev/null || echo "No .deb produced (VM unavailable); source tree ready at ${BUILD}/${PKG}-${VER}"
