"""Phonemize utterances with espeak (1.47) into one normalized IPA inventory.

Each word type is phonemized once (espeak --ipa=3 separates phonemes with "_"), then
utterances are mapped word by word. The normalization is fixed in prereg/prereg.md:
strip stress and length marks, remove ties and ZWJ, merge rhotics (ɾ ɹ ʁ ʀ r) into "r".
Output: CSV with text and phon, where phon is "(p h o n) (p h o n)", one bracketed group per word,
which is the input format CLASSIC expects.

Usage: python -I src/input/11_phonemize.py <in.csv> <out.csv> <espeak_voice: en-us|de> [max_utts]
"""

import csv
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

STRIP = str.maketrans("", "", "ˈˌːˑ‍͜͡")
RHOTICS = {"ɾ": "r", "ɹ": "r", "ʁ": "r", "ʀ": "r", "r": "r", "ɐ̯": "ɐ"}


SPLIT = {"ɚ": ["ə", "r"], "əl": ["ə", "l"]}


def normalize(segments):
    out = []
    for seg in segments:
        seg = seg.translate(STRIP)
        if not seg or (seg.startswith("(") and seg.endswith(")")):   # espeak language-switch marks, e.g. "(en)"
            continue
        if seg in SPLIT:
            out.extend(SPLIT[seg])
            continue
        if len(seg) > 1 and seg.endswith("ɚ"):                     # aɪɚ -> aɪ ə r
            out.extend([seg[:-1], "ə", "r"])
            continue
        seg = RHOTICS.get(seg, seg)
        if len(seg) > 1 and seg[-1] in "ɹɾʁr":                     # r-coloured vowels: oɹ -> o r
            out.extend([seg[:-1], "r"])
            continue
        out.append(seg)
    return out


def phonemize_word(word: str, voice: str):
    res = subprocess.run(["espeak", "-q", "--ipa=3", "-v", voice, word],
                         capture_output=True, text=True, timeout=30)
    segs = [s for part in res.stdout.split() for s in part.split("_")]
    return normalize(segs)


def main(in_csv: str, out_csv: str, voice: str, max_utts: str = "0") -> None:
    with open(in_csv, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if int(max_utts):
        rows = rows[: int(max_utts)]
    types = sorted({w for r in rows for w in r["text"].split()})
    with ThreadPoolExecutor(max_workers=8) as ex:
        lex = dict(zip(types, ex.map(lambda w: phonemize_word(w, voice), types)))
    empty = [w for w, p in lex.items() if not p]
    from pathlib import Path
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["file", "speaker", "text", "phon"])
        for r in rows:
            groups = [lex[w] for w in r["text"].split() if lex.get(w)]
            if groups:
                wr.writerow([r["file"], r["speaker"], r["text"], " ".join("(" + " ".join(g) + ")" for g in groups)])
    with open(out_csv.replace(".csv", "_lexicon.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["word", "phon", "count"])
        counts = {}
        for r in rows:
            for w in r["text"].split():
                counts[w] = counts.get(w, 0) + 1
        for w in types:
            if lex[w]:
                wr.writerow([w, " ".join(lex[w]), counts.get(w, 0)])
    inventory = sorted({s for p in lex.values() for s in p})
    print(f"utterances={len(rows)} word_types={len(types)} empty_types={len(empty)} inventory={len(inventory)}")
    print("inventory:", " ".join(inventory))


if __name__ == "__main__":
    main(*sys.argv[1:5])
