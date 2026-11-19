"""Fidelity check: noun and verb types learned by CLASSIC on Thomas, against the paper's Figure 2.

Learned word chunks (phoneme strings) are mapped back to spellings through the phonemizer lexicon.
For homophones, the most frequent spelling is used. Spellings are matched to %mor stems by exact form,
then by stripping common inflections. Target (Fig 2 xlsx, CLASSIC, Thomas, stage 10): Noun 2958, Verb 836.
Pass: both counts within +-15%.
Usage: python -I src/analysis/15_fidelity.py <lex.txt> <lexicon.csv> <pos.csv> <out.csv>
"""

import csv
import sys

TARGET = {"Noun": 2958, "Verb": 836}
SUFFIXES = ("", "s", "es", "ies", "ing", "ed", "d", "'s")


def main(lex_txt, lexicon_csv, pos_csv, out_csv) -> int:
    best = {}
    with open(lexicon_csv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = int(r["count"])
            if r["phon"] not in best or n > best[r["phon"]][1]:
                best[r["phon"]] = (r["word"], n)
    with open(pos_csv, encoding="utf-8") as fh:
        pos = {r["stem"]: r["category"] for r in csv.DictReader(fh)}

    def category(word):
        for suf in SUFFIXES:
            if suf and not word.endswith(suf):
                continue
            stem = word[: len(word) - len(suf)] if suf else word
            for cand in (stem, stem + "e", stem[:-1] if len(stem) > 2 and stem[-1] == stem[-2] else None,
                         stem[:-1] + "y" if suf == "ies" else None):
                if cand and cand in pos:
                    return pos[cand]
        return None

    learned = [p for p in open(lex_txt, encoding="utf-8").read().split("\n") if p]
    counts = {"Noun": 0, "Verb": 0, "other": 0, "unmapped": 0}
    for p in learned:
        if p not in best:
            counts["unmapped"] += 1
            continue
        counts[category(best[p][0]) or "other"] += 1
    rows = []
    for cat, tgt in TARGET.items():
        ok = abs(counts[cat] - tgt) <= 0.15 * tgt
        rows.append(dict(category=cat, ours=counts[cat], paper=tgt, ratio=round(counts[cat] / tgt, 3), passed=ok))
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"learned_lex={len(learned)} other={counts['other']} unmapped={counts['unmapped']}")
    for r in rows:
        print(r)
    return 0 if all(r["passed"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
