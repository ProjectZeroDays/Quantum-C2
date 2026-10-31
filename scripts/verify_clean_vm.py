"""Clean-VM verification — checks builds on untrusted OS."""
import subprocess, sys
errors = []
for mod in ["core", "bus", "rat", "web"]:
    r = subprocess.run(f"python -c \"import quantum.{mod}; print('OK')\"", shell=True)
    if r.returncode != 0:
        errors.append(f"{mod}: import failed")
if errors:
    print("CLEAN-VM FAILED:", "; ".join(errors))
    sys.exit(1)
print("CLEAN-VM PASSED")
