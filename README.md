# xrate-classic

Does shared word form lower the input a bilingual learner needs? This repo tests the question in two steps on the CLASSIC model of child word learning.

1. **Reproduction.** Refit the noun-bias model of Jones, Cabiddu, Aros Muñoz, Roeser, Du & Rowland (2026), *Revisiting the noun bias*, JEP: General 155(9), using the authors' shared data (OSF [gxqvd](https://osf.io/gxqvd)). Target: the English vs German noun-verb contrast, 0.849 for children and 0.549 for the model.
2. **Extension.** Feed CLASSIC mixed English and German input at controlled ratios. Vary whether translation equivalents share their form. Fit the exposure ratio at which L2 words are learned, following the design in *Facts Follow the Spelling* (Otegen, ACL Rolling Review 2026). The plan is fixed in `prereg/prereg.md` before any simulation.

CLASSIC.py and the authors' data are downloaded from OSF at build time and are not redistributed, because the OSF project sets no licence.

```
make env      # micromamba env from env/environment.yml, plus bambi from prebuilt wheels
make repro    # fetch OSF files, refit in Python, read the authors' saved brms fit (exit 1 if the refit misses the target)
```
Logs go to `logs/`. The refit uses bambi/PyMC with the authors' brms formula and priors. `src/repro/01_fit_childmodel.R` is the brms route, kept for machines where Stan compiles.

## Reproduction result (2026-11-17)
| Contrast: English vs German [noun - verb] | Paper (brms) | This refit (bambi) |
|---|---|---|
| Children | 0.849 [0.654, 1.043] | 0.847 [0.652, 1.041] |
| CLASSIC model | 0.549 [0.356, 0.748] | 0.549 [0.353, 0.743] |

4 chains x 3,000 draws, max R-hat 1.005, min bulk ESS 714, 0 divergences.
