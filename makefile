.PHONY: setup install clean vscode
.PHONY: help
.PHONY: all

help:
	@echo "Usage: make <target> [VARIABLE=value]"
	@echo ""
	@echo "Targets:"
	@echo "  setup            Create and set up the Conda environment"
	@echo "  update           Update the Conda environment"
	@echo "  clean            Remove the Conda environment"
	@echo "  export           Export the Conda environment to a .yml file"
	@echo "  submodules       Initialize and install submodule packages"
	@echo "  nexus            Run the BCNexus model"
	@echo "  nexus_plots      Generate Nexus plots"
	@echo "  plots            Generate scenario plots (runs nexus_plots)"
	@echo ""
	@echo "Variables:"
	@echo "  NEXUS_SCENARIO   Name of the Nexus scenario (default: 'Base_CNZ_noCCS')"
	@echo "  PYPSA_YEAR       Year for PyPSA simulation (default: 2035)"
	@echo "  NEXUS_TIMESLICES Number of timeslices (default: 24)"
	@echo ""
	@echo "Examples:"
	@echo "  make nexus NEXUS_SCENARIO=CNZ_1"
	@echo "  make nexus_plots NEXUS_SCENARIO=CNZ_1 NEXUS_TIMESLICES=96"

# Default values for variables
PYPSA_YEAR ?= 2035
NEXUS_SCENARIO ?= 'Base_CNZ_noCCS'
NEXUS_TIMESLICES ?= 24

# Create and activate env, install dependencies
setup:
	@echo "Creating and setting up the environment..."
	conda env create -f env/environment.yml
	@echo "Installing local package..."
	pip install -e.
	git submodule init
	@echo "Environment created. Please restart your shell or run 'conda activate wb_oemc' manually."

# Update the environment
update:
	@echo "Updating environment..."
	conda env update -f env/environment.yml
	@echo "Environment updated. Please restart your shell or run 'conda activate wb_oemc' manually."

# Optional: clean up env (if you want this)
clean:
	@echo "Removing the environment..."
	conda env remove -n bc_nexus
	@echo "Environment removed."

export:
	@echo "Exporting the environment..."
	conda env export -n bc_nexus > env/environment.yml
	@echo "Environment exported to env/environment.yml."

# submodules:
# 	# Initialize and update all submodules recursively
# 	echo "Initializing and updating submodules..."
# 	git submodule update --init --recursive || true

# 	# Navigate to the Linking_tool submodule and install it
# 	echo "Installing packages from setup.py..."; \
# 	[ -f models/BC_Nexus/setup.py ] && pip install -e models/BC_Nexus || echo "setup.py not found in models/BC_Nexus"; \

# 	echo "Submodules initialized and packages installed successfully."
# 	# git submodule status

# dash: # Doesn't run with SFU VPN, need to find alterative proven ways to shwocase locally
# 	python bc_combined_modelling/vis/dashboard/app.py

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
	make about_nexus_scenarios
	python workflow/scripts/plot_results_BCNexus.py $(NEXUS_SCENARIO) $(NEXUS_TIMESLICES)	

plots:
	@echo "Creating scenario plots..."
	make nexus_plots
# python workflow/scripts/bccm_scenario_plots.py $(YEAR) $(TIMESLICES)