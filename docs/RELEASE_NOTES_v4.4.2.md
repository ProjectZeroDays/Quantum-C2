# QUANTUM-CLI v4.4.2

Maintenance release — fixes the on-device AI model download and aligns the
Android app version with the release tag.

## Fixes

- **Local AI model download (HTTP 401 / 404)** — both model mirrors baked
  into the app died: Google retired the `mediapipe-assets` bucket path for
  `gemma-2b-it-gpu-int4.bin` (404) and the `litert-community` HuggingFace
  fallback became auto-gated (anonymous downloads get HTTP 401). The
  downloader now uses three verified ungated HuggingFace mirrors of the same
  Gemma-2B int4 TFLite artifact (~1.3 GB, GPU int4 first, CPU int4
  fallbacks), all confirmed anonymously downloadable, with resume + mirror
  failover unchanged.
- Downloads now send a proper `User-Agent` so mirrors don't throttle or
  reject default Java clients.
- **Version alignment** — the Android `versionName` was still `4.4.0`
  (versionCode 2) inside the v4.4.1 APKs, so the in-app update check kept
  offering v4.4.1. Now `4.4.2` (versionCode 3), matching this tag.

## Other changes since v4.4.1

- The Python-side `sim/` simulation package (red/blue/purple team + network
  simulation, training tooling) was removed from the app per operator
  decision; it was never part of the operational C2 path. Suite: 117
  passed, 2 skipped.

## Notes

- Local AI needs ~1.3 GB free space; the download resumes automatically if
  interrupted. Online and deterministic AI modes are unaffected.
