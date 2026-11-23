# Pre-registration: shared form and the bilingual exchange rate in CLASSIC

Status: DRAFT v2 (2026-11-19). Freeze by committing before any extension simulation runs. Frozen in commit `79e5b7b` (2026-11-19 13:09 UTC). It was first recorded as `be595af`, and the authorship email was rewritten to a personal address before publishing, with identical content and date.

## Background
In *Facts Follow the Spelling*, facts learned from Cyrillic Kazakh moved English answers only 11 to 34% as much as English text did. Shared name spellings raised this to 70 to 80%, and one changed consonant per name cut English-Turkish transfer from 79% to 16%. CLASSIC (Jones et al. 2026) learns only by chunking phoneme sequences and has no semantics. So the only route by which input in one language can help the other is **form overlap**. This makes CLASSIC a form-only baseline for the cognate advantage reported in bilingual toddlers.

## Change from v1 (made before any simulation)
v1 had "shared form in a fraction f of L2 tokens" arms. In CLASSIC, a target that is identical to an English word is learned from English input alone, so those dose arms would be flat by construction and uninformative. v2 replaces them with (a) an identical-form positive control and (b) a graded test on each word's natural phonological overlap.

## Hypotheses
- **H1 (near-identical form helps).** Targets whose form is the English word with one consonant changed reach 50% learned at a lower L2 share (r50) than targets in their native German form.
- **H2 (graded cognate effect).** Within the native arm, the probability that a target is learned increases with its natural phonological overlap with its English equivalent, controlling for L2 token count.
- **Control.** Identical-form targets are learned at near-ceiling across the grid, because English input alone teaches them. If they are not, the pipeline is broken.

## Design
- **Input:** caregiver speech from CHILDES Thomas (English, MOT+FAT) and Leo (German, MUT+VAT), phonemized with espeak 1.47 into one normalized IPA inventory (see `src/input/11_phonemize.py`). Total fixed at 40,000 utterances.
- **Ratio grid:** L2:L1 odds of 1/16, 1/8, 1/4, 1/2, 1, 2, 4, 8 and 16, with 5 seeds each (45 runs).
- **Targets:** 150 German nouns and verbs with English equivalents from the MUSE de-en dictionary, frequency-stratified (`data/interim/te_pairs.csv`). Each run randomly assigns 50 to each arm: native, onecons, identical.
- **Outcome:** whether the target form exists as a word-level (lex) chunk at the end of input.

## Analysis
- **Fit 1:** a binomial logistic of learned against log2(odds), per arm. r50 = 2^(-a/b).
- **Fit 2 (H2):** a logistic of learned against natural_overlap + log(1 + L2 tokens), native arm only.
- **Exchange rate τ:** in the onecons arm, τ = β(log(1 + L1 tokens of the English source form)) / β(log(1 + L2 tokens of the target)), from one logistic.
- **CI:** cluster bootstrap over words and seeds, 2,000 replicates, percentile 95% intervals.
- **Decision rules:**
  - H1 is supported if the 95% CI of r50(native)/r50(onecons) lies above 1.
  - H2 is supported if the 95% CI of the overlap slope lies above 0.
- **Falsification:** an r50 ratio CI that includes 1, or an overlap slope CI that includes 0.

## Fidelity check (before the extension)
On Thomas (first 210,748 MOT utterances), compare the noun and verb types learned with Figure 2 of Jones et al. (CLASSIC, stage 10: 2958 nouns, 836 verbs), with a tolerance of ±15%. Nouns and verbs are approximated from the %mor tier, because the authors' category file is not shared.

## Known limitations
- MUSE translations are noisy (e.g. starten -> launch). CLASSIC has no semantics, so a mistranslation changes which English form counts as the source, not the learning mechanics. Report a manually audited subset.
- One speaker per language (Thomas, Leo), so input register differs between the languages.

## Fidelity result (2026-11-19, before the grid)
- **Pre-specified check: FAILED.** CLASSIC on Thomas learned 3,913 noun and 1,371 verb surface types, against the paper's 2,958 and 836 (ratios 1.32 and 1.64, tolerance ±15%). Surface types are the paper's unit ("kick, kicked, kicks = three word types").
- **Diagnostic (post hoc, labelled as such).** The same noun/verb categorization applied to Thomas's own speech over the same sessions gives 2,602 nouns and 732 verbs, against the paper's 1,958 and 463 (ratios 1.33 and 1.58). The overshoot is the same for the child as for the model, so it comes from our %mor-based categorization, not from CLASSIC. The model-to-child ratio matches the paper: nouns 1.504 vs 1.511, verbs 1.873 vs 1.806.
- **Consequence.** The extension's outcome is defined by target forms, not by noun/verb categories, so the categorization mismatch does not affect H1 or H2. Proceed, and report both numbers.

## Results (2026-11-19, analysis exactly as pre-registered, commit 79e5b7b)
45 runs, 6,750 target outcomes, 2,000 cluster-bootstrap replicates.
| Statistic | Estimate | 95% CI |
|---|---|---|
| r50 native (German share for 50% learned) | 0.179 | 0.123 to 0.254 |
| r50 onecons | 0.127 | 0.073 to 0.192 |
| r50 ratio native / onecons (H1) | 1.41 | 0.86 to 2.52 |
| Overlap slope, native arm (H2) | -0.35 | -2.42 to 1.63 |
| Exchange rate tau, onecons | 0.05 | -0.05 to 0.15 |
| Share learned, identical-form control | 0.88 | 0.82 to 0.93 |
- **H1 not supported.** The point estimate favours near-identical forms, and the advantage is concentrated at low German exposure (figure: 36% vs 27% learned at 1:16). But the CI includes 1.
- **H2 not supported.** There is no graded effect of natural phonological overlap.
- **The control behaved as expected**, so the pipeline is sound.
- **Interpretation.** A form-only chunking learner gains at most a small, uncertain benefit from near-identical cross-language forms (tau about 0.05: one English token of the source form is worth about 0.05 German tokens of the target). In the ACL experiments on language models, one changed consonant cut transfer from 79% to 16%, so form gated transfer strongly there. If bilingual toddlers show a robust cognate advantage, form overlap in a chunking learner is not enough to explain it. This points to meaning-mediated routes (translation equivalents linked through concepts).
