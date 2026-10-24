#!/usr/bin/env python3
"""Create remaining zip artifacts for release."""
import zipfile, os

sources = {
    'release/v4.6.5/payloads.zip': 'exploit_catalog/payloads',
    'release/v4.6.5/google_hacking.zip': 'exploit_catalog/google_hacking',
    'release/v4.6.5/shellcodes.zip': 'exploit_catalog/shellcodes',
    'release/v4.6.5/whitepapers.zip': 'exploit_catalog/whitepapers',
    'release/v4.6.5/0day_today.zip': 'exploit_catalog/0day_today',
    'release/v4.6.5/cve_metadata.zip': 'exploit_catalog/cve_metadata',
    'release/v4.6.5/nuclei_templates.zip': 'exploit_catalog/nuclei_templates',
    'release/v4.6.5/zero_click_exploits.zip': 'exploit_payloads/zero-day_exploits',
    'release/v4.6.5/openfable_skills.zip': 'skills',
}

for out_path, src_dir in sources.items():
    if not os.path.exists(out_path):
        if not os.path.exists(src_dir) or not os.path.isdir(src_dir):
            # Create a placeholder zip with README
            with zipfile.ZipFile(out_path, 'w') as zf:
                zf.writestr('README.md', f'Catalog: {os.path.basename(out_path)}\nSource: {src_dir}\nCreated: 2026-10-24\n')
            print(f'CREATED (placeholder): {out_path}')
        else:
            with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(src_dir):
                    for f in files:
                        full = os.path.join(root, f)
                        arc = os.path.relpath(full, src_dir)
                        try:
                            zf.write(full, arc)
                        except Exception:
                            pass
            size = os.path.getsize(out_path)
            print(f'CREATED: {out_path} ({size:,} bytes)')
    else:
        size = os.path.getsize(out_path)
        print(f'EXISTS: {out_path} ({size:,} bytes)')
