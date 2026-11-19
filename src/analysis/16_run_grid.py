"""Run the pre-registered grid: 9 L2:L1 odds x 5 seeds, each = mix -> CLASSIC -> score targets.

Each run writes results/grid/<tag>/ (CLASSIC outputs) and results/grid/scored-<tag>.csv.
Runs in parallel (default 7 workers). Completed runs are skipped, so the grid can be resumed.
Usage: python src/analysis/16_run_grid.py [workers=7] [total_utts=40000]
"""

import csv
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ODDS = ["1/16", "1/8", "1/4", "1/2", "1", "2", "4", "8", "16"]
SEEDS = [1, 2, 3, 4, 5]
PY = sys.executable


def one_run(odds: str, seed: int, total: int) -> str:
    tag = f"o{odds.replace('/', '_')}-s{seed}"
    scored = Path(f"results/grid/scored-{tag}.csv")
    if scored.exists():
        return f"{tag} skipped (done)"
    log = open(f"logs/grid/{tag}.log", "w")
    subprocess.run([PY, "-I", "src/input/14_mix.py", odds, str(seed), str(total), "data/interim/mixes"],
                   stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run([PY, "src/classic/run_classic.py", f"data/interim/mixes/mix-{tag}.csv",
                    f"results/grid/{tag}", tag, str(seed)], stdout=log, stderr=subprocess.STDOUT, check=True)
    learned = set(Path(f"results/grid/{tag}/lex-{tag}.txt").read_text(encoding="utf-8").split("\n"))
    with open(f"data/interim/mixes/targets-{tag}.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r.update(odds=odds, seed=seed, learned=int(r["target"] in learned))
    with open(scored, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    by_arm = {a: sum(r["learned"] for r in rows if r["arm"] == a) for a in ("native", "onecons", "identical")}
    return f"{tag} done learned={by_arm}"


def main(workers: str = "7", total: str = "40000") -> None:
    Path("logs/grid").mkdir(parents=True, exist_ok=True)
    Path("results/grid").mkdir(parents=True, exist_ok=True)
    jobs = [(o, s) for s in SEEDS for o in ODDS]
    with ProcessPoolExecutor(max_workers=int(workers)) as ex:
        futs = {ex.submit(one_run, o, s, int(total)): (o, s) for o, s in jobs}
        for f in as_completed(futs):
            try:
                print(f.result(), flush=True)
            except Exception as e:  # report and continue, so one failure does not kill the grid
                print(f"{futs[f]} FAILED: {e}", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:3])
