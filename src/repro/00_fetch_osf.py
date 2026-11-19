"""Download the files needed for the reproduction from OSF project gxqvd.

Files are treated as data only. Nothing downloaded is executed.
Usage: python -I src/repro/00_fetch_osf.py data/raw/osf
"""

import json
import sys
import urllib.request
from pathlib import Path

NODE = "gxqvd"
WANTED = {
    "Fig 2 child model vocab data.xlsx",
    "noun_verb_diff_CHILDMODEL_model_NEGBINOMIAL.rds",
    "noun_bias_analysis_v4.Rmd",
    "CLASSIC.py",
    "README.txt",
}


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def walk(url: str):
    while url:
        page = get_json(url)
        for item in page["data"]:
            attrs = item["attributes"]
            if attrs["kind"] == "folder":
                yield from walk(item["relationships"]["files"]["links"]["related"]["href"])
            else:
                yield attrs["name"], item["links"]["download"]
        url = page["links"].get("next")


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    found = set()
    for name, href in walk(f"https://api.osf.io/v2/nodes/{NODE}/files/osfstorage/"):
        if name in WANTED and name not in found:
            dest = out / name
            urllib.request.urlretrieve(href, dest)
            found.add(name)
            print(f"downloaded {name} ({dest.stat().st_size} bytes)")
    missing = WANTED - found
    if missing:
        sys.exit(f"missing on OSF: {sorted(missing)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/raw/osf")
