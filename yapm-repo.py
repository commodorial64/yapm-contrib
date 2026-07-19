#!/usr/bin/env python3
import json
import os
import subprocess
import tarfile
import tempfile
import re
import ast

def parse_yapm_data(content: str) -> dict:
    data = {"METADATA": {}, "CONTENT": {}, "FILES": {}}
    current_section = None

    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('//'): continue
        if '//' in line: line = line.split('//')[0].strip()

        if line.startswith('[') and line.endswith(']'):
            current_section = line[1:-1]
            continue

        if current_section and '=' in line:
            parts = line.split('=', 1)
            key = parts[0].strip().strip('"').strip("'")
            val = parts[1].strip()

            if val.startswith('[') and val.endswith(']'):
                try: val = ast.literal_eval(val)
                except Exception: val = []
            else:
                val = val.strip('"').strip("'")

            data[current_section][key] = val
    return data

def read_yapm_data(path: str) -> str:
    with open(path, 'rb') as f:
        magic = f.read(4)

    if magic == b'PK\x03\x04':
        import zipfile
        with zipfile.ZipFile(path, 'r') as zf:
            if 'yapm.data' not in zf.namelist():
                return None
            return zf.read('yapm.data').decode('utf-8')
    elif magic == b'\x28\xb5\x2f\xfd':
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(['zstd', '-d', '-f', path, '-o', f'{td}/pkg.tar'],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with tarfile.open(f'{td}/pkg.tar') as tar:
                names = tar.getnames()
                data_file = next((n for n in names if n.endswith('yapm.data')), None)
                if not data_file:
                    return None
                return tar.extractfile(data_file).read().decode('utf-8')
    else:
        return None

def build_repo():
    print("Building YAPM repository index...")
    index = {"packages": {}}

    for item in sorted(os.listdir('.')):
        if not item.endswith('.yapm'):
            continue
        print(f"Scanning {item}...")
        try:
            content = read_yapm_data(item)
            if content is None:
                print(f"  Warning: {item} does not contain yapm.data")
                continue

            y_data = parse_yapm_data(content)
            meta = y_data.get("METADATA", {})
            name = meta.get("name")
            if not name:
                print(f"  Warning: {item} has no name in METADATA. Skipping.")
                continue

            author = meta.get("author", "")
            key = f"{author}/{name}" if author else name
            version = meta.get("version", "0.0.0")

            if key not in index["packages"]:
                index["packages"][key] = {
                    "latest": version,
                    "versions": {}
                }

            pkg_entry = index["packages"][key]
            if version > pkg_entry["latest"]:
                pkg_entry["latest"] = version

            pkg_entry["versions"][version] = {
                "description": meta.get("description", ""),
                "author": author or "Unknown",
                "license": meta.get("license", "Unknown"),
                "dependencies": meta.get("dependencies", []),
                "filename": item
            }

            display = f"{author}@{name}" if author else name
            print(f"  Added {display} v{version} ({item})")
        except Exception as e:
            print(f"  Error reading {item}: {e}")

    with open('index.json', 'w') as f:
        json.dump(index, f, indent=4)

    total = sum(len(v["versions"]) for v in index["packages"].values())
    print(f"\nSuccessfully generated index.json with {len(index['packages'])} packages ({total} versions).")

if __name__ == '__main__':
    build_repo()
