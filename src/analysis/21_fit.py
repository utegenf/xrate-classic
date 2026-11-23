"""Pre-registered analysis of the grid (prereg/prereg.md v2).

Fit 1: per arm, logistic learned ~ log2(odds). r50 = 2^(-a/b). H1: r50(native) / r50(onecons) > 1.
Fit 2: native arm, logistic learned ~ natural_overlap + log1p(l2_tokens). H2: overlap slope > 0.
Exchange rate tau (onecons arm): beta(log1p(L1 tokens of English source)) / beta(log1p(L2 tokens of target)).
CI: cluster bootstrap over words and seeds, 2,000 replicates, percentile 95%.
Usage: python src/analysis/21_fit.py [n_boot=2000]
"""

import glob
import sys
import warnings
from fractions import Fraction
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import statsmodels.api as sm

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

warnings.simplefilter("ignore")
OUT = Path("results/tables")


def load() -> pd.DataFrame:
    df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("results/grid/scored-*.csv"))], ignore_index=True)
    df["log2_odds"] = df["odds"].astype(str).map(lambda o: float(np.log2(float(Fraction(o)))))
    df["log_l2"] = np.log1p(df["l2_tokens"])
    df["log_l1_en"] = np.log1p(df["l1_tokens_en"])
    return df


def logit(y, X):
    return sm.GLM(y, sm.add_constant(X), family=sm.families.Binomial()).fit().params.values


def stats(df: pd.DataFrame) -> dict:
    out = {}
    for arm in ("native", "onecons", "identical"):
        d = df[df.arm == arm]
        out[f"p_learned_{arm}"] = d.learned.mean()
        if d.learned.nunique() == 2:
            a, b = logit(d.learned, d[["log2_odds"]])
            out[f"r50_{arm}"] = 2 ** (-a / b) if b > 0 else np.nan
        else:
            out[f"r50_{arm}"] = np.nan
    out["r50_ratio_native_over_onecons"] = out["r50_native"] / out["r50_onecons"]
    nat = df[df.arm == "native"]
    out["overlap_slope_native"] = logit(nat.learned, nat[["natural_overlap", "log_l2"]])[1]
    one = df[df.arm == "onecons"]
    _, b_l1, b_l2 = logit(one.learned, one[["log_l1_en", "log_l2"]])
    out["tau_onecons"] = b_l1 / b_l2
    return out


def bootstrap(df: pd.DataFrame, n_boot: int, seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    words, seeds = df["de"].unique(), df["seed"].unique()
    by = {k: g for k, g in df.groupby(["de", "seed"])}
    reps = []
    for _ in range(n_boot):
        ws, ss = rng.choice(words, len(words)), rng.choice(seeds, len(seeds))
        parts = [by[(w, s)] for w in ws for s in ss if (w, s) in by]
        try:
            reps.append(stats(pd.concat(parts, ignore_index=True)))
        except Exception:
            continue
    return pd.DataFrame(reps)


def main(n_boot: str = "2000") -> None:
    df = load()
    print(f"rows={len(df)} runs={df.groupby(['odds', 'seed']).ngroups}")
    point = stats(df)
    boot = bootstrap(df, int(n_boot))
    rows = []
    for k, v in point.items():
        lo, hi = np.nanpercentile(boot[k], [2.5, 97.5])
        rows.append(dict(statistic=k, estimate=v, ci_lo=lo, ci_hi=hi, n_boot_ok=int(boot[k].notna().sum())))
    res = pd.DataFrame(rows)
    ratio = res.set_index("statistic").loc["r50_ratio_native_over_onecons"]
    slope = res.set_index("statistic").loc["overlap_slope_native"]
    res.loc[len(res)] = dict(statistic="H1_supported", estimate=float(ratio.ci_lo > 1), ci_lo=np.nan, ci_hi=np.nan, n_boot_ok=0)
    res.loc[len(res)] = dict(statistic="H2_supported", estimate=float(slope.ci_lo > 0), ci_lo=np.nan, ci_hi=np.nan, n_boot_ok=0)
    print(res.round(3).to_string(index=False))
    res.to_csv(OUT / "extension_results.csv", index=False)

    curve = df.groupby(["arm", "log2_odds"]).learned.mean().unstack(0)
    fig, ax = plt.subplots(figsize=(5, 3.5))
    for arm, style in (("identical", ":"), ("onecons", "-"), ("native", "--")):
        ax.plot(curve.index, curve[arm], style, marker="o", label=arm)
    ax.set_xlabel("German:English input odds (log2)")
    ax.set_ylabel("share of targets learned")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    Path("results/figures").mkdir(parents=True, exist_ok=True)
    fig.savefig("results/figures/extension_curves.png", dpi=200)


if __name__ == "__main__":
    main(*sys.argv[1:2])
