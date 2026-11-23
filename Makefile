ENV ?= xrate-classic
export MAMBA_ROOT_PREFIX ?= $(HOME)/micromamba
RUN := micromamba run -n $(ENV)
OSF := data/raw/osf

.PHONY: all env repro fetch clean

all: repro

# conda-forge env, then bambi from prebuilt wheels only (on hosts with glibc 2.26 and gcc 7, pip would otherwise try to build numpy and llvmlite from source and fail).
env:
	micromamba create -y -f env/environment.yml
	$(RUN) pip install --only-binary=:all: bambi openpyxl

fetch: $(OSF)/.done
$(OSF)/.done:
	mkdir -p logs $(OSF)
	$(RUN) python -I src/repro/00_fetch_osf.py $(OSF) 2>&1 | tee logs/00_fetch_osf.log
	touch $@

# Reproduction: refit in Python (bambi/PyMC) and compare with the paper. Also print the authors' saved brms fit.
repro: results/tables/repro_childmodel_bambi.csv results/tables/saved_fit_contrasts.csv
results/tables/repro_childmodel_bambi.csv: $(OSF)/.done src/repro/01b_fit_childmodel_bambi.py
	$(RUN) python src/repro/01b_fit_childmodel_bambi.py $(OSF) results/tables 2>&1 | tee logs/01_fit_childmodel_bambi.log
results/tables/saved_fit_contrasts.csv: $(OSF)/.done src/repro/02_read_saved_fit.R
	$(RUN) Rscript src/repro/02_read_saved_fit.R $(OSF) results/tables 2>&1 | tee logs/02_read_saved_fit.log

clean:
	rm -rf data/interim results/tables/* results/figures/*
