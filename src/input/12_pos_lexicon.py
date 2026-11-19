"""Build a noun/verb lexicon from the CHAT %mor tiers of the caregiver speakers.

%mor gives POS|stem tokens (e.g. "noun|dog", "verb|thank-Fin-..."). For each stem we count noun vs verb
uses and keep the majority category. This approximates the authors' category file, which is not shared.
Usage: python -I src/input/12_pos_lexicon.py <corpus_dir> <out.csv> <SPK>[,<SPK>...]
"""

import collections
import csv
import re
import sys
from pathlib import Path


def main(corpus_dir: str, out_csv: str, speakers: str) -> None:
    spk = set(speakers.split(","))
    counts = collections.defaultdict(collections.Counter)
    for f in sorted(Path(corpus_dir).rglob("*.cha")):
        cur = None
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("*"):
                cur = line[1:4]
            elif line.startswith("%mor:") and cur in spk:
                for tok in line[5:].split():
                    pos, _, stem = tok.partition("|")
                    if pos in ("noun", "verb") and stem:
                        stem = re.split(r"[-&]", stem)[0].lower()
                        counts[stem][pos] += 1
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stem", "category", "n_noun", "n_verb"])
        for stem, c in sorted(counts.items()):
            w.writerow([stem, "Noun" if c["noun"] >= c["verb"] else "Verb", c["noun"], c["verb"]])
    cats = collections.Counter("Noun" if c["noun"] >= c["verb"] else "Verb" for c in counts.values())
    print(f"stems={len(counts)} nouns={cats['Noun']} verbs={cats['Verb']}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
