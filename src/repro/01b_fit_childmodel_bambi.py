"""Python refit (bambi/PyMC) of the noun-bias model in Jones et al. (2026).

Mirrors the brms specification in the authors' noun_bias_analysis_v4.Rmd:
  outcome ~ category * language * data_source + (1 | child), negative binomial,
  priors b ~ N(0, 2.5), Intercept ~ t3(6.5, 2.5), shape ~ InvGamma(0.4, 0.3), sd ~ t3(0, 2.5),
  4 chains, seed 123. brms and PyMC use the same NB dispersion (var = mu + mu^2 / shape).

Target (OSF analysis report), English[noun - verb] VS German[noun - verb]:
  Child 0.849 (95% CI 0.654 to 1.043). Model 0.549 (0.356 to 0.748).
Pass: estimate within +-0.02 and CI bounds within +-0.03.

Usage: python src/repro/01b_fit_childmodel_bambi.py data/raw/osf results/tables
"""

import sys
from pathlib import Path

import bambi as bmb
import numpy as np
import pandas as pd

TARGETS = {"child": (0.849, 0.654, 1.043), "model": (0.549, 0.356, 0.748)}


def load(raw_dir: Path) -> pd.DataFrame:
    df = pd.read_excel(raw_dir / "Fig 2 child model vocab data.xlsx")
    df = df[df["data_source"].isin(["Child", "CLASSIC"]) & (df["stage"] == 10)].copy()
    df = df.rename(columns={"Category": "category", "cumfreq": "outcome"})
    df["data_source"] = df["data_source"].map({"Child": "Child", "CLASSIC": "Model"})
    df["category"] = pd.Categorical(df["category"], categories=["Noun", "Verb"])
    df["language"] = pd.Categorical(df["language"], categories=["English", "German", "Spanish", "Mandarin"])
    df["data_source"] = pd.Categorical(df["data_source"], categories=["Child", "Model"])
    df["child"] = df["child"].astype(str)
    df["outcome"] = df["outcome"].astype(int)
    return df[["outcome", "category", "language", "data_source", "child"]]


def draws_for(post, term: str, **coords) -> np.ndarray:
    da = post[term]
    dim = [d for d in da.dims if d not in ("chain", "draw")][0]
    labels = [str(x) for x in da[dim].values]
    wanted = ", ".join(coords.values())
    idx = [i for i, lab in enumerate(labels) if lab.replace(" ", "") == wanted.replace(" ", "")]
    if len(idx) != 1:
        raise KeyError(f"{term}: could not find {wanted} in {labels}")
    return da.isel({dim: idx[0]}).values.ravel()


def main(raw_dir: str, out_dir: str) -> int:
    raw, out = Path(raw_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df = load(raw)
    print(f"rows={len(df)} children={df['child'].nunique()}")
    print(df.groupby(["data_source", "language", "category"], observed=True)["outcome"].describe()[["count", "mean"]])

    priors = {
        "common": bmb.Prior("Normal", mu=0, sigma=2.5),
        "Intercept": bmb.Prior("StudentT", nu=3, mu=6.5, sigma=2.5),
        "alpha": bmb.Prior("InverseGamma", alpha=0.4, beta=0.3),
        "1|child": bmb.Prior("Normal", mu=0, sigma=bmb.Prior("HalfStudentT", nu=3, sigma=2.5)),
    }
    model = bmb.Model(
        "outcome ~ category * language * data_source + (1 | child)",
        df, family="negativebinomial", priors=priors,
    )
    idata = model.fit(draws=3000, tune=3000, chains=4, cores=4, random_seed=123, target_accept=0.95)
    post = idata.posterior
    print("terms:", [v for v in post.data_vars])

    import arviz as az
    summ = az.summary(idata, var_names=[v for v in post.data_vars if v != "1|child"], kind="diagnostics")
    n_div = int(idata.sample_stats["diverging"].sum())
    max_rhat, min_ess = float(summ["r_hat"].max()), float(summ["ess_bulk"].min())
    print(f"diagnostics: max_rhat={max_rhat:.4f} min_ess_bulk={min_ess:.0f} divergences={n_div}")
    print(summ.sort_values("r_hat", ascending=False).head(5))
    converged = max_rhat <= 1.01 and min_ess >= 400 and n_div == 0

    child = draws_for(post, "category:language", category="Verb", language="German")
    model_extra = draws_for(post, "category:language:data_source", category="Verb", language="German", data_source="Model")
    rows = []
    for name, d in (("child", child), ("model", child + model_extra)):
        est, lo, hi = float(d.mean()), float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))
        t_est, t_lo, t_hi = TARGETS[name]
        ok = abs(est - t_est) <= 0.02 and abs(lo - t_lo) <= 0.03 and abs(hi - t_hi) <= 0.03
        rows.append(dict(row=name, est=est, se=float(d.std()), lo=lo, hi=hi,
                         est_paper=t_est, lo_paper=t_lo, hi_paper=t_hi, passed=ok and converged,
                         max_rhat=max_rhat, min_ess_bulk=min_ess, divergences=n_div, backend="bambi/pymc"))
    res = pd.DataFrame(rows)
    print(res.round(3).to_string(index=False))
    res.to_csv(out / "repro_childmodel_bambi.csv", index=False)
    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "data/raw/osf",
                  sys.argv[2] if len(sys.argv) > 2 else "results/tables"))
