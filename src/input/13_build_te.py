"""Build the German-English translation-equivalent (TE) target list.

German candidates: word types in Leo caregiver speech that are noun or verb lemmas in the %mor tier
(majority category), with at least MIN_FREQ tokens. English equivalent: the MUSE de-en dictionary
entry (Conneau et al. 2018) that occurs in Thomas caregiver speech with the same category, choosing the
most frequent. Pairs whose phoneme strings are already identical are dropped. Natural overlap is the
normalized phoneme edit similarity between the native German form and the English form.

Output: 150 pairs, frequency-stratified on German token count.
Usage: python -I src/input/13_build_te.py <out.csv> [n=150] [seed=7]
"""

import csv
import random
import sys
from collections import defaultdict

MIN_FREQ = 20
P = "data/interim/"


def read(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def edit_sim(a, b):
    a, b = a.split(), b.split()
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return 1 - d[len(b)] / max(len(a), len(b))


def main(out_csv, n="150", seed="7"):
    n, rng = int(n), random.Random(int(seed))
    de_lex = {r["word"]: (r["phon"], int(r["count"])) for r in read(P + "phonemized/leo_full_lexicon.csv")}
    en_lex = {r["word"]: (r["phon"], int(r["count"])) for r in read(P + "phonemized/thomas_full_lexicon.csv")}
    de_pos = {r["stem"].lower(): r["category"] for r in read(P + "childes/leo_pos.csv")}
    en_pos = {r["stem"].lower(): r["category"] for r in read(P + "childes/thomas_pos.csv")}
    muse = defaultdict(list)
    with open("data/raw/muse/de-en.txt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) == 2:
                muse[parts[0]].append(parts[1])

    pairs, used_en = [], set()
    for de, (de_phon, de_n) in sorted(de_lex.items(), key=lambda kv: -kv[1][1]):
        cat = de_pos.get(de)
        if cat is None or de_n < MIN_FREQ:
            continue
        cands = [e for e in muse.get(de, []) if e in en_lex and en_pos.get(e) == cat and e != de and e not in used_en]
        if not cands:
            continue
        en = max(cands, key=lambda e: en_lex[e][1])
        en_phon = en_lex[en][0]
        if en_phon == de_phon or len(en_phon.split()) < 2:
            continue
        used_en.add(en)
        pairs.append(dict(de=de, en=en, category=cat, de_phon=de_phon, en_phon=en_phon,
                          de_freq=de_n, en_freq=en_lex[en][1], natural_overlap=round(edit_sim(de_phon, en_phon), 3)))
    # frequency-stratified sample: split candidates into 5 German-frequency bins, take n/5 from each
    pairs.sort(key=lambda p: p["de_freq"])
    k = len(pairs) // 5
    chosen = []
    for b in range(5):
        bin_ = pairs[b * k:(b + 1) * k] if b < 4 else pairs[4 * k:]
        chosen += rng.sample(bin_, min(n // 5, len(bin_)))
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=chosen[0].keys())
        w.writeheader()
        w.writerows(chosen)
    nouns = sum(p["category"] == "Noun" for p in chosen)
    print(f"candidates={len(pairs)} chosen={len(chosen)} nouns={nouns} verbs={len(chosen) - nouns} "
          f"mean_overlap={sum(p['natural_overlap'] for p in chosen) / len(chosen):.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
