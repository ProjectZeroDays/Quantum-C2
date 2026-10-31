# Packaging Release Notes — v4.6.5
Formats produced by VM / container build scripts (authorized only):
- packaging/dist/*.deb — dpkg-deb / debian container
- packaging/dist/*.dmg — macOS hdiutil / Unix VM
- packaging/dist/*.ipa — iOS companion agent payload (authorized mobile)
- packaging/dist/*.snap — snapcraft snap (classic confinement for network/camera)
- packaging/dist/*.flatpak — flatpak-builder (org.freedesktop.Platform 23.08)
Run: bash packaging/build-all-vm.sh (VM/docker/macOS host required)
Note: All packaging is authorized-engagement-only. No simulated behavior.
