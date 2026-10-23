#!/usr/bin/env python3
"""Extract verified native prerequisites from pinned images without starting containers."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime_directory", type=Path, help="New private runtime directory; must not exist")
    args = parser.parse_args()
    runtime = args.runtime_directory.resolve()
    runtime.mkdir(mode=0o700)  # Fail rather than replace any existing directory.
    (runtime / "bin").mkdir(mode=0o700)
    records = json.loads(Path(__file__).with_name("binaries.json").read_text())
    images = sorted({row["image"].split(":")[0] + "@" + row["imageId"] for row in records})
    for image in images:
        subprocess.run(["docker", "pull", "--platform", "linux/amd64", image], check=True, timeout=300)
    receipts = []
    for row in records:
        image = row["image"].split(":")[0] + "@" + row["imageId"]
        container = subprocess.check_output(["docker", "create", "--network", "none", image, "/bin/true"], text=True, timeout=30).strip()
        try:
            destination = runtime / "bin" / Path(row["source"]).name
            subprocess.run(["docker", "cp", container + ":" + row["source"], str(destination)], check=True, timeout=60)
            actual = hashlib.sha256(destination.read_bytes()).hexdigest()
            if actual != row["sha256"]:
                destination.unlink()
                raise RuntimeError("Extracted SHA-256 mismatch: " + row["source"])
            destination.chmod(0o700)
            receipts.append({"image": image, "source": row["source"], "sha256": actual})
        finally:
            # Only this never-started container is removed, including on failure.
            subprocess.run(["docker", "rm", container], check=True, timeout=30)
    (runtime / "bootstrap-receipt.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print("Verified four private runtime binaries in", runtime)


if __name__ == "__main__":
    main()
