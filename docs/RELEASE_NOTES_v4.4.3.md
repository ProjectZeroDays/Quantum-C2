# QUANTUM-CLI v4.4.3

Operator-suite feature release — camera feeds, Tasks workflows, floating
chat, zenmap scan controls, and real chat attachments.

## Camera video thumbnails + live feed preview

- Every camera card now shows a **real JPEG still** as a 2×2-inch
  clickable thumbnail with a **centered play button** — cyan when the
  camera is CONTROLLED (creds cracked), dim when riding the
  default-credential path.
- Tapping opens a **full-screen video feed preview**: live stills
  auto-refreshing every 3s over the camera's snapshot endpoints, LIVE
  on/off toggle, manual refresh, per-frame timestamps, and honest
  NO SIGNAL / FETCHING states (no fake video).
- Thumbnails re-fetch after PTZ nudges and preview close so they never
  show a stale view. New `ops/CamPreview.kt` engine (two-pass
  inSampleSize decode, thumbnail cache, per-IP in-flight guard).

## Tasks dashboard (workflows)

- New **Tasks** sidebar page: create, edit, delete, and run named
  chains of `/ai` commands with `${var}` templating (a `scan` step
  auto-fills `first_host` / `first_cam` for later steps).
- Runs stop at the first failed step and report per-step results.
  Seeded with recon-then-fingerprint / zero-check / camwar chains.

## Floating chat bubble

- A cyan bubble in the bottom-right corner opens the popup AI chat from
  any page (hidden on the Chat page itself).

## Zenmap-style scan controls (Network page)

- Host scan with target CIDR or single host, port spec including ranges
  (`22,80,443,1000-2000`), and nmap timing templates **T0 paranoid →
  T5 insane** mapped to sweep concurrency and probe timeout.
- Camera/ONVIF ports (554/8899) light up green in the results.
  Pure logic unit-tested in `ops/ZenScan.kt`.

## Chat attachments + save-as

- Paperclip opens the **system file picker** (any file) or
  **photo/video picker**; the new image icon goes straight to photos.
  Picked files are copied into `files/attachments`; small text files
  are inlined into the message so every AI mode can read them.
- The download icon on each message now opens a **save-as dialog** —
  any location, name, and extension — instead of a fixed
  `files/Downloads/*.txt`.

## Also

- In-app manual entries 13–17 documenting all of the above.
- All 67 Android JVM unit tests green; both APK flavors build clean.
