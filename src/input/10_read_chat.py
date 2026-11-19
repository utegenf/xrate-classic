"""Extract caregiver utterances from CHILDES CHAT transcripts as clean orthographic text.

Files are read as data only. Output: one utterance per row (file, speaker, text).
Usage: python -I src/input/10_read_chat.py <corpus_dir> <out.csv> <SPK>[,<SPK>...]
  English (Thomas): MOT,FAT    German (Leo): MUT,VAT
"""

import csv
import re
import sys
from pathlib import Path

DROP_TOKEN = re.compile(r"^(xxx|yyy|www|0\S*|&\S*|\+\S*|\(\.+\)|[.?!,;:\"„“”‡]+)$")


def clean(text: str) -> str:
    text = re.sub(r"\x15[^\x15]*\x15", " ", text)       # media bullets
    text = re.sub(r"\b\d+_\d+\b", " ", text)            # bare time stamps
    text = re.sub(r"\[[^\]]*\]", " ", text)             # [/], [: x], [=! x], [*] ...
    text = re.sub(r"[<>]", " ", text)                   # retracing brackets, keep inner words
    text = text.replace("_", " ")                       # compounds written with _
    words = []
    for tok in text.split():
        if DROP_TOKEN.match(tok):
            continue
        tok = re.sub(r"@\S*$", "", tok)                 # @f, @c, @l special-form markers
        tok = tok.replace("(", "").replace(")", "")     # (be)cause -> because
        tok = re.sub(r"[:^ˈˌ↫↑↓≠≈]", "", tok)          # lengthening, prosody marks
        tok = re.sub(r"[^\w'\-]", "", tok)
        if tok and not tok.isdigit():
            words.append(tok.lower())
    return " ".join(words)


def utterances(path: Path, speakers: set):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    cur_spk, cur = None, []
    for line in lines + ["*END:"]:
        if line.startswith("\t") and cur_spk:           # continuation of the current tier
            cur.append(line.strip())
            continue
        if cur_spk in speakers and cur:
            yield cur_spk, " ".join(cur)
        cur_spk, cur = None, []
        if line.startswith("*") and ":" in line:
            spk, _, rest = line[1:].partition(":")
            cur_spk, cur = spk, [rest.strip()]


def main(corpus_dir: str, out_csv: str, speakers: str) -> None:
    spk = set(speakers.split(","))
    files = sorted(Path(corpus_dir).rglob("*.cha"))
    n_in = n_out = 0
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "speaker", "text"])
        for f in files:
            for s, raw in utterances(f, spk):
                n_in += 1
                txt = clean(raw)
                if txt:
                    w.writerow([f.name, s, txt])
                    n_out += 1
    print(f"{corpus_dir}: files={len(files)} utterances_in={n_in} kept={n_out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
