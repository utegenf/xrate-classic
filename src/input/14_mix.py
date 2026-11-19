"""Build one mixed English (L1) + German (L2) CLASSIC input for a given L2:L1 odds and seed.

Targets: the 150 TE pairs, randomly assigned within each run to three arms of 50:
  native     German input keeps the German form. Target = German form.
  onecons    German input uses the English form with one consonant changed. Target = that form.
  identical  German input uses the English form unchanged. Target = English form (positive control).
Utterances are sampled without replacement from each corpus and shuffled together.

Writes <out_dir>/mix-o<odds>-s<seed>.csv (column phon) and targets-o<odds>-s<seed>.csv with
per-target L2 token counts, L1 token counts of the target form, and L1 counts of the English source form.
Usage: python -I src/input/14_mix.py <odds> <seed> <total_utts> <out_dir>
"""

import csv
import random
import sys
from fractions import Fraction
from pathlib import Path

P = "data/interim/"
CONSONANTS = list("bdfɡhjklmnprstvwz") + ["ʃ", "ŋ"]


def read(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def one_consonant(phon: str, rng: random.Random) -> str:
    segs = phon.split()
    idx = [i for i, s in enumerate(segs) if s in CONSONANTS]
    i = rng.choice(idx) if idx else 0
    segs[i] = rng.choice([c for c in CONSONANTS if c != segs[i]])
    return " ".join(segs)


def groups(phon_field: str):
    return [g.strip("() ") for g in phon_field.split(") (")]


def main(odds: str, seed: str, total: str, out_dir: str) -> None:
    odds_f, seed_i, total_i = Fraction(odds), int(seed), int(total)
    rng = random.Random(seed_i)
    p_l2 = odds_f / (1 + odds_f)
    n_l2 = round(total_i * float(p_l2))
    n_l1 = total_i - n_l2

    en = read(P + "phonemized/thomas_full.csv")
    de = read(P + "phonemized/leo_full.csv")
    te = read(P + "te_pairs.csv")
    order = list(range(len(te)))
    rng.shuffle(order)
    arms = {}
    for k, i in enumerate(order):
        arm = ("native", "onecons", "identical")[k % 3]
        t = te[i]
        target = {"native": t["de_phon"], "onecons": one_consonant(t["en_phon"], rng), "identical": t["en_phon"]}[arm]
        arms[t["de"]] = dict(de=t["de"], en=t["en"], arm=arm, target=target, en_phon=t["en_phon"],
                             de_phon=t["de_phon"], natural_overlap=t["natural_overlap"], l2_tokens=0)

    l1 = rng.sample(en, n_l1)
    l2 = rng.sample(de, n_l2)
    utts = []
    for r in l2:
        words, gs = r["text"].split(), groups(r["phon"])
        if len(words) == len(gs):
            for j, w in enumerate(words):
                if w in arms:
                    gs[j] = arms[w]["target"]
                    arms[w]["l2_tokens"] += 1
        utts.append("(" + ") (".join(gs) + ")")
    utts += [r["phon"] for r in l1]
    rng.shuffle(utts)

    l1_forms = {}
    for r in l1:
        for g in groups(r["phon"]):
            l1_forms[g] = l1_forms.get(g, 0) + 1
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tag = f"o{odds.replace('/', '_')}-s{seed_i}"
    with open(out / f"mix-{tag}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["phon"])
        w.writerows([u] for u in utts)
    with open(out / f"targets-{tag}.csv", "w", newline="", encoding="utf-8") as fh:
        fields = ["de", "en", "arm", "target", "natural_overlap", "l2_tokens", "l1_tokens_target", "l1_tokens_en"]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for a in arms.values():
            w.writerow(dict(de=a["de"], en=a["en"], arm=a["arm"], target=a["target"],
                            natural_overlap=a["natural_overlap"], l2_tokens=a["l2_tokens"],
                            l1_tokens_target=l1_forms.get(a["target"], 0), l1_tokens_en=l1_forms.get(a["en_phon"], 0)))
    print(f"{tag}: p_l2={float(p_l2):.3f} l2_utts={n_l2} l1_utts={n_l1}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
