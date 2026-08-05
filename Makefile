# BCNexus — task shortcuts.
# Run from the repository root: the Python code resolves config/ and data/
# relative to the working directory, and the package lives in codebase/.
#
#   make help
#   make index
#   make solve SCEN=Base_CNZ_noCCS HG=4 NC=1 THREADS=16
#
# Sections:
#   1. environment   conda env lifecycle                (unchanged)
#   2. legacy        workflow/scripts entry points      (unchanged)
#   3. pipeline      bcnexus.stages CLI                 (new)
#   4. reporting     master report index                (new)
#
# Windows: `make` is not installed by default. Use Git Bash / WSL, install it
# (`conda install -c conda-forge make`), or use make.bat.

.PHONY: help setup update clean export submodules vscode all
.PHONY: nexus about_nexus_scenarios nexus_plots plots
.PHONY: build overlay datafile lp solve results run workflow
.PHONY: index index-all reindex clean-index

# ---------------------------------------------------------------- variables
# Legacy variables (kept, same names and defaults as before)
NEXUS_SCENARIO   ?= 'Base_CNZ_noCCS'
NEXUS_TIMESLICES ?= 24

# Stage-CLI variables — keep free of trailing comments, make keeps the spaces.
# VIS   folder holding the CLEW_*.html reports
# SCEN  scenario key in config/scenarios_bcnexus.yaml
# ALGO  Kotzur | Niet     HG  hour grouping     NC  number of clusters
PY        ?= python
VIS       ?= vis
INDEX     ?= report/BCNexus_report_v1.html
SCEN      ?= Base_CNZ_noCCS
ALGO      ?= Kotzur
HG        ?= 4
NC        ?= 1
SOLVER    ?= gurobi
THREADS   ?= 16

export PYTHONPATH := codebase$(if $(PYTHONPATH),:$(PYTHONPATH),)

STAGE = $(PY) -m bcnexus.stages
ARGS  = -s $(SCEN) -a $(ALGO) -hg $(HG) -nc $(NC)

# ---------------------------------------------------------------- help
help:
	@echo "Usage: make <target> [VARIABLE=value]"
	@echo ""
	@echo "Environment:"
	@echo "  setup            Create and set up the Conda environment"
	@echo "  update           Update the Conda environment"
	@echo "  clean            Remove the Conda environment"
	@echo "  export           Export the Conda environment to a .yml file"
	@echo "  submodules       Initialize and install submodule packages"
	@echo ""
	@echo "Legacy model entry points (workflow/scripts):"
	@echo "  nexus            Run the BCNexus model"
	@echo "  nexus_plots      Generate Nexus plots"
	@echo "  plots            Generate scenario plots (runs nexus_plots)"
	@echo ""
	@echo "Stage pipeline (bcnexus.stages — resumable, Snakemake-facing):"
	@echo "  build            Stages 1-3: builder -> temporal -> storage schema"
	@echo "  overlay          Stage 4a: apply scenario overrides"
	@echo "  datafile         Stage 4b: CSVs -> otoole datafile"
	@echo "  lp               Stage 5: datafile -> .lp (glpsol)"
	@echo "  solve            Stage 6: .lp -> .sol"
	@echo "  results          Stage 7: .sol -> result CSVs + report, then reindex"
	@echo "  run              Full pipeline for one scenario"
	@echo "  workflow         Run the Snakemake matrix (codebase/workflow_v3)"
	@echo ""
	@echo "Reporting:"
	@echo "  index            Rebuild the master report index -> $(INDEX)"
	@echo "  index-all        Same, also scanning sub-folders (dated run dirs)"
	@echo "  clean-index      Delete the index only (reports untouched)"
	@echo ""
	@echo "Variables:"
	@echo "  NEXUS_SCENARIO   Legacy scenario name  (default: $(NEXUS_SCENARIO))"
	@echo "  NEXUS_TIMESLICES Legacy timeslices     (default: $(NEXUS_TIMESLICES))"
	@echo "  SCEN ALGO HG NC SOLVER THREADS VIS  -> $(SCEN) $(ALGO) $(HG) $(NC) $(SOLVER) $(THREADS) $(VIS)"
	@echo "  INDEX            Master index output   (default: $(INDEX))"
	@echo ""
	@echo "Examples:"
	@echo "  make nexus NEXUS_SCENARIO=CNZ_1"
	@echo "  make nexus_plots NEXUS_SCENARIO=CNZ_1 NEXUS_TIMESLICES=96"
	@echo "  make run SCEN=Base_CNZ_noCCS HG=4 NC=1 THREADS=16"
	@echo "  make index"

# ---------------------------------------------------------------- 1. environment
# Create and activate env, install dependencies
setup:
	@echo "Creating and setting up the environment..."
	conda env create -f env/environment.yml
	@echo "Installing local package..."
	pip install -e .
	git submodule init
	@echo "Environment created. Please restart your shell or run 'conda activate bc_nexus' manually."

# Update the environment
update:
	@echo "Updating environment..."
	conda env update -f env/environment.yml
	@echo "Environment updated. Please restart your shell or run 'conda activate bc_nexus' manually."
	@echo "Installing local package..."
	pip install -e .

# Optional: clean up env
clean:
	@echo "Removing the environment..."
	conda env remove -n bc_nexus
	@echo "Environment removed."

export:
	@echo "Exporting the environment..."
	conda env export -n bc_nexus > env/environment.yml
	@echo "Environment exported to env/environment.yml."

submodules:
	@echo "Initializing submodules..."
	git submodule update --init --recursive

# ---------------------------------------------------------------- 2. legacy
nexus:
	@echo "Running BC Nexus model with 'workflow/scripts/BCNexus.py'..."
	$(MAKE) about_nexus_scenarios
	python workflow/scripts/BCNexus.py

# resources:
# 	@echo "Running RESource builder workflow and resource assessment model with 'workflow/scripts/BCResource.py'..."
# 	python workflow/scripts/BC_RESource.py

about_nexus_scenarios:
	python workflow/scripts/scenario_pipeline.py show_nexus_scenarios

nexus_plots:
	$(MAKE) about_nexus_scenarios
	python workflow/scripts/plot_results_BCNexus.py $(NEXUS_SCENARIO) $(NEXUS_TIMESLICES)

plots:
	@echo "Creating scenario plots..."
	$(MAKE) nexus_plots
# python workflow/scripts/bccm_scenario_plots.py $(YEAR) $(TIMESLICES)

# ---------------------------------------------------------------- 3. pipeline
build:
	@$(STAGE) build $(ARGS)

overlay:
	@$(STAGE) scenario-overlay $(ARGS)

datafile:
	@$(STAGE) datafile $(ARGS)

lp:
	@$(STAGE) lp $(ARGS)

solve:
	@$(STAGE) solve $(ARGS) --solver $(SOLVER) --threads $(THREADS)

results:
	@$(STAGE) results $(ARGS) --solver $(SOLVER)
	@$(MAKE) index

run: build overlay datafile lp solve results

workflow:
	@snakemake -s codebase/workflow_v3/Snakefile \
	          --configfile codebase/workflow_v3/config.yaml -j 1
	@$(MAKE) index

# ---------------------------------------------------------------- 4. reporting
index:
	@$(PY) -m bcnexus.vis.index $(VIS) $(INDEX)

index-all:
	@$(PY) -m bcnexus.vis.index $(VIS) $(INDEX) --recursive

reindex: index

clean-index:
	@rm -f $(INDEX) && echo "removed $(INDEX)"
