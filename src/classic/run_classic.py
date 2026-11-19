"""Run the authors' CLASSIC.py (downloaded from OSF, unmodified) on one phonemized input file.

CLASSIC.py imports two modules the authors did not share: `hashtable` and `phon_convert_final`.
Stand-ins live in src/classic/stubs/. All behavioural tests (NWR, LWL, CDI, BPVS) are switched off,
because their stimulus files are not shared either. Only learning is run, and its per-utterance log is kept.

Usage: python src/classic/run_classic.py <phonemized.csv> <out_dir> <subject_name> [seed] [max_utts]
Writes <out_dir>/learning-<subject>-LR100-acc450.csv (CLASSIC's own format) and prints the wall time.
"""

import importlib.util
import sys
import time
import warnings
from pathlib import Path

# CLASSIC's chained .iat assignment emits a pandas FutureWarning on every utterance (about 30 MB per run).
# The assignment works under pandas 2, so silence only that warning category.
warnings.simplefilter("ignore", FutureWarning)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "classic" / "stubs"))
CLASSIC_PATH = ROOT / "data" / "raw" / "osf" / "CLASSIC.py"


def load_classic():
    # CLASSIC.py ends with a top-level setup() call that prompts on stdin. Execute the
    # unmodified file but skip that one line, so its functions and globals can be driven directly.
    src = CLASSIC_PATH.read_text(encoding="utf-8")
    lines = src.splitlines()
    assert lines.count("setup()") == 1, "expected exactly one top-level setup() call"
    src = "\n".join(line for line in lines if line != "setup()")
    spec = importlib.util.spec_from_loader("CLASSIC", loader=None, origin=str(CLASSIC_PATH))
    mod = importlib.util.module_from_spec(spec)
    exec(compile(src, str(CLASSIC_PATH), "exec"), mod.__dict__)
    mod.test_nwr = mod.test_lwl = mod.test_vocab = mod.test_speech_perception = False
    mod.confusion_matrix = False
    mod.debugging = mod.testing = mod.timing = False
    mod.chunks = mod.HashTable(size=100000)
    return mod


def main(phon_csv: str, out_dir: str, subject: str, seed: str = "1", max_utts: str = "0") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(phon_csv)
    if int(max_utts):
        df = df.head(int(max_utts))
    xlsx = out / f"input-{subject}.xlsx"
    pd.DataFrame({"Input": df["phon"]}).to_excel(xlsx, index=False)

    mod = load_classic()
    np.random.seed(int(seed))
    mod.random.seed(int(seed))
    empty = pd.DataFrame({"phonemic": pd.Series([], dtype=object)})
    handles = [open(out / f"{n}-{subject}.csv", "w", encoding="utf-8") for n in ("nwr", "overall", "speech")]
    t0 = time.time()
    mod.train_model(str(xlsx), str(out) + "/", f"{subject}-LR100-acc450", f"{subject},100,450,",
                    *([empty] * 9), *handles)
    secs = time.time() - t0
    for h in handles:
        h.close()
    # Learned word-level chunks, one phoneme string per line (CLASSIC keys look like "d ɑ ɡ.lex").
    lex_words = sorted(k.rsplit(".", 1)[0] for k in mod.chunks.keys() if k.endswith("." + mod.ck_lexical))
    (out / f"lex-{subject}.txt").write_text("\n".join(lex_words) + "\n", encoding="utf-8")
    print(f"subject={subject} utterances={len(df)} seconds={secs:.1f} "
          f"sublex={mod.sublex_vocab} lex={mod.lex_vocab} multiword={mod.multiword_vocab}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
