#!/usr/bin/env python3
import sys, subprocess, tarfile, tempfile

pkg = sys.argv[1]

with open(pkg, "rb") as f:
    magic = f.read(4)
if magic != b"\x28\xb5\x2f\xfd":
    print(f"\u274c {pkg} is not a valid tar.zst file")
    sys.exit(1)

with tempfile.TemporaryDirectory() as td:
    subprocess.run(["zstd", "-d", "-f", pkg, "-o", f"{td}/pkg.tar"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = tarfile.open(f"{td}/pkg.tar")
    names = [n.split("/")[-1] for n in t.getnames()]
    if "yapm.data" not in names:
        print(f"\u274c {pkg} is missing yapm.data")
        sys.exit(1)
    data_file = next(n for n in t.getnames() if n.endswith("yapm.data"))
    content = t.extractfile(data_file).read().decode()
    t.close()

lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("//")]
required = ["name", "version", "description", "author", "license"]
missing = [f for f in required if not any(l.startswith(f + " =") for l in lines)]
if missing:
    print(f"\u274c {pkg} is missing required fields: {', '.join(missing)}")
    sys.exit(1)

print(f"\u2705 {pkg} looks good")
