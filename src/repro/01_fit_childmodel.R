# Refit the noun-bias model from Jones et al. (2026), JEP: General 155(9), using
# the authors' shared data (OSF gxqvd). The specification is copied from
# noun_bias_analysis_v4.Rmd (negative binomial section).
#
# Target (OSF analysis report):
#   Child English[noun - verb] VS German[noun - verb]: 0.849 (SE 0.100, 95% CI 0.654 to 1.043)
#   Model English[noun - verb] VS German[noun - verb]: 0.549 (SE 0.100, 95% CI 0.356 to 0.748)
# Pass: each estimate within +-0.02, each CI bound within +-0.03.
#
# Usage: Rscript src/repro/01_fit_childmodel.R data/raw/osf results/tables

suppressPackageStartupMessages({
  library(readxl); library(dplyr); library(stringr); library(brms)
})

args <- commandArgs(trailingOnly = TRUE)
raw_dir <- if (length(args) >= 1) args[1] else "data/raw/osf"
out_dir <- if (length(args) >= 2) args[2] else "results/tables"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
backend <- if (requireNamespace("cmdstanr", quietly = TRUE)) "cmdstanr" else "rstan"

df <- read_excel(file.path(raw_dir, "Fig 2 child model vocab data.xlsx")) %>%
  filter(data_source %in% c("Child", "CLASSIC")) %>%
  rename(category = Category) %>%
  mutate(category = case_when(category == "Noun" ~ "Noun", category == "Verb" ~ "Verb"),
         data_source = case_when(data_source == "Child" ~ "Child", data_source == "CLASSIC" ~ "Model")) %>%
  filter(stage == 10) %>%
  rename(outcome = cumfreq) %>%
  mutate(language = factor(language, levels = c("English", "German", "Spanish", "Mandarin")),
         category = factor(category, levels = c("Noun", "Verb")),
         data_source = factor(data_source, levels = c("Child", "Model")))

priors <- c(
  set_prior("normal(0, 2.5)", class = "b"),
  set_prior("student_t(3, 6.5, 2.5)", class = "Intercept"),
  set_prior("inv_gamma(0.4, 0.3)", class = "shape"),
  set_prior("student_t(3, 0, 2.5)", class = "sd")
)

fit <- brm(
  formula = bf(outcome ~ category * language * data_source + (1 | child)),
  data = df, family = negbinomial(), prior = priors, sample_prior = "yes",
  chains = 4, cores = 4, seed = 123, refresh = 0, backend = backend
)
saveRDS(fit, file.path(out_dir, "refit_childmodel_negbin.rds"))

hyps <- c(
  child = "categoryVerb:languageGerman = 0",
  model = "categoryVerb:languageGerman + categoryVerb:languageGerman:data_sourceModel = 0"
)
target <- data.frame(row = c("child", "model"), est = c(0.849, 0.549),
                     lo = c(0.654, 0.356), hi = c(1.043, 0.748))

res <- hypothesis(fit, hyps, seed = 123)$hypothesis
out <- data.frame(row = names(hyps), est = res$Estimate, se = res$Est.Error,
                  lo = res$CI.Lower, hi = res$CI.Upper) %>%
  left_join(target, by = "row", suffix = c("", "_paper")) %>%
  mutate(pass = abs(est - est_paper) <= 0.02 & abs(lo - lo_paper) <= 0.03 & abs(hi - hi_paper) <= 0.03,
         backend = backend)
print(out, digits = 3)
write.csv(out, file.path(out_dir, "repro_childmodel.csv"), row.names = FALSE)

# Same contrasts from the authors' saved fit, if present, to separate data issues from sampler noise.
saved <- file.path(raw_dir, "noun_verb_diff_CHILDMODEL_model_NEGBINOMIAL.rds")
if (file.exists(saved)) {
  ref <- hypothesis(readRDS(saved), hyps, seed = 123)$hypothesis
  print(data.frame(row = names(hyps), saved_est = ref$Estimate, saved_lo = ref$CI.Lower, saved_hi = ref$CI.Upper), digits = 3)
}
if (!all(out$pass)) quit(status = 1)
