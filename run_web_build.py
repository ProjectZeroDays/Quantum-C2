import os, subprocess
os.makedirs('build/web/dist', exist_ok=True)
with open('build/web/dist/index.html', 'w') as f:
    f.write('<!DOCTYPE html><html><head><title>QUANTUM CLI v4.5.1 Web</title></head><body><h1>QUANTUM-CLI v4.5.1 Web Bundle</h1><h2>/swarm /goal /push command reference</h2><p>Authorized engagements only. --no-ai path preserved.</p></body></html>')
# Copy docs/reference files
for src in ['README.md', 'quantum_cli.py', 'add_push_swarm_doc.md']:
    if os.path.exists(src):
        import shutil
        shutil.copy(src, 'build/web/dist/' + src)
print('build/web/dist contents:')
for item in os.listdir('build/web/dist'):
    sz = os.path.getsize(os.path.join('build/web/dist', item))
    print(' ', item, sz)
