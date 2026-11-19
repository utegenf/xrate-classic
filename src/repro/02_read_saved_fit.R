# Read the authors' saved brms fit (OSF gxqvd) and print the published contrasts.
# No Stan compilation is needed. This checks the target numbers at the source.
# Usage: Rscript src/repro/02_read_saved_fit.R data/raw/osf results/tables

suppressPackageStartupMessages(library(brms))
args <- commandArgs(trailingOnly = TRUE)
raw_dir <- if (length(args) >= 1) args[1] else "data/raw/osf"
out_dir <- if (length(args) >= 2) args[2] else "results/tables"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

fit <- readRDS(file.path(raw_dir, "noun_verb_diff_CHILDMODEL_model_NEGBINOMIAL.rds"))
hyps <- c(
  child = "categoryVerb:languageGerman = 0",
  model = "categoryVerb:languageGerman + categoryVerb:languageGerman:data_sourceModel = 0"
)
h <- hypothesis(fit, hyps, seed = 123)$hypothesis
out <- data.frame(row = names(hyps), est = h$Estimate, se = h$Est.Error, lo = h$CI.Lower, hi = h$CI.Upper)
print(out, digits = 3)
write.csv(out, file.path(out_dir, "saved_fit_contrasts.csv"), row.names = FALSE)
