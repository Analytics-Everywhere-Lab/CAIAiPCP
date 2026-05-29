#####################################
#
# Customizable settings 
#
#####################################

# Build Version
VERSION := v0.0.1

# Build environment destination.
# Option here is : l_dev
BUILD_DEST := l_dev

# Trivy scanning options
TRIVY_SEVERITY ?= HIGH,CRITICAL
DEFAULT_SCAN_ENVS := cp_mcp


#####################################
#
# Fixed settings
#
#####################################

# Define the path to be added (using := for simple expansion)
PROJECT_ROOT := $(PWD)/../

# Python and docker source directory
SRC_DIR := $(PROJECT_ROOT)/src

# Export the variable to the environment for all commands
PYTHONPATH := $(PYTHONPATH):$(PROJECT_ROOT)/src

# Define the path to docker/podman env file
ENV_FILE := $(PWD)/env_files/$(BUILD_DEST).env

# Include the environment file. This file is for non-private settings. 
# Use the typical .env file for private settings.
include $(ENV_FILE)

# Force Make to use Bash
SHELL := /bin/bash

# Target-Specific Assignments (Mandatory per target)
# These Conda environments must exist locally on the development box.
# Used for local development. See l_conda_create_* targets to create the Conda environments.
l_run_mcp_server: CONDA_ENV = cp_mcp
l_run_mcp_tests: CONDA_ENV = cp_mcp
l_run_mcp_inspector: CONDA_ENV = cp_mcp

# Validates that a target-specific CONDA_ENV variable is explicitly set,
# sources Conda's shell integration script, and activates the environment.
CONDA_ACTIVATE = \
	if [ -z "$(CONDA_ENV)" ]; then echo "ERROR: CONDA_ENV is not defined for this target!"; exit 1; fi; \
	source $(shell conda info --base)/etc/profile.d/conda.sh; conda activate $(CONDA_ENV)

# Export all variables defined in this Makefile and the ENV_FILE
# to child processes (like podman-compose and others)
export

.PHONY: \
	help \
	l_print_env \
	l_run_mcp_server \
	l_run_mcp_tests \
	l_run_mcp_inspector \
	l_conda_create_all \
	l_conda_remove_all \
	l_mcp_library_scan \
	l_recreate_db \
	l_run_db_cli

.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "================ LOCAL DEVELOPMENT TARGETS ================"
	@awk '/^l_[a-zA-Z_-]+:.*?##/ { \
		helpMessage = substr($$0, index($$0, "##") + 3); \
		target = $$1; sub(/:.*/, "", target); \
		printf "\033[36m%-28s\033[0m %s\n", target, helpMessage \
	}' $(MAKEFILE_LIST)

l_print_env: ## Print exported environment variables visible to targets
	@echo ""
	@echo "================ EXPORTED ENVIRONMENT ================"
	@env | sort | more

l_recreate_db: ## Re-creates sqllite database. sqllite should already be installed on OSX
	@echo "Recreating Database ... "; \
	rm -fR $(PWD)/../db/aip.db; \
	cd $(PWD)/.././util_scripts; \
	sh init_db.sh; \
	echo "Complete"

l_run_db_cli: ## Connects to the database using the sqllite cli.
	@cd $(PWD)/.././util_scripts; \
	sh cli.sh; \

l_conda_create_cp_mcp:
	$(call CREATE_ENV,cp_mcp,$(PWD)/../)

l_conda_create_all: ## Creates all local Conda environments
	$(MAKE) l_conda_create_cp_mcp

define CREATE_ENV
	@set -e; \
	if [ -z "$(1)" ]; then \
		echo "ERROR: Missing CONDA_ENV name!"; \
		exit 1; \
	fi; \
	TARGET_DIR="$(2)"; \
	if [ -z "$${TARGET_DIR}" ]; then TARGET_DIR="."; fi; \
	if [ ! -f "$${TARGET_DIR}/requirements.txt" ]; then \
		echo "ERROR: requirements.txt not found at: $${TARGET_DIR}/requirements.txt"; \
		exit 1; \
	fi; \
	if conda env list | grep -q "^$(1) "; then \
		echo "Skipping: Conda environment '$(1)' already exists."; \
	else \
		echo "Creating conda environment: $(1)..."; \
		conda create -n $(1) python=3.13.3 pip --channel conda-forge --override-channels -y; \
		echo "Installing dependencies from $${TARGET_DIR}/requirements.txt into $(1)..."; \
		conda run -n $(1) pip install -r "$${TARGET_DIR}/requirements.txt"; \
	fi
endef

l_conda_remove_cp_mcp:
	$(call REMOVE_ENV,cp_mcp)

l_conda_remove_all: ## Removes all Conda environments
	$(MAKE) l_conda_remove_cp_mcp

define REMOVE_ENV
	@set -e; \
	echo "Attempting to remove conda environment: $(1)..."; \
	conda env remove -n $(1) -y || true
endef

l_run_mcp_server: l_conda_create_cp_mcp ## Run the MCP server locally for development
	@ ( \
		set -e; \
		$(CONDA_ACTIVATE) ; \
		echo "Conda Prefix: $$CONDA_PREFIX" ; \
		echo " ... will run mcp server startup script..." ; \
	)

l_run_mcp_inspector: ## Runs MCP inspector
	@ (\
		set -e; \
		npx @modelcontextprotocol/inspector; \
	)

l_run_mcp_tests: l_conda_create_cp_mcp ## Run the MCP service-related unit tests locally for development
	@ ( \
		set -e; \
		$(CONDA_ACTIVATE) ; \
		echo "Conda Prefix: $$CONDA_PREFIX" ; \
		echo " ... will run mcp service-related unit tests ..." ; \
	)

# Define the fallback scan modifier if not overridden via command line
SCAN_TARGET ?= default
TRIVY_TEMP_LOCK := requirements.lock


l_mcp_library_scan: l_conda_remove_all l_conda_create_all ## Run Trivy scan across specified or default Conda environments
	@rm -f $(TRIVY_TEMP_LOCK)
	@\
	if [ "$(SCAN_TARGET)" = "default" ]; then \
		envs=($(DEFAULT_SCAN_ENVS)); \
	else \
		envs=("$(SCAN_TARGET)"); \
	fi; \
	echo "Target environments to scan: $${envs[*]}"; \
	for env in "$${envs[@]}"; do \
		if conda env list | grep -q "$${env} "; then \
			echo "-> Activating and freezing $${env}..."; \
			source $$(conda info --base)/etc/profile.d/conda.sh && conda activate $${env} && pip freeze >> $(TRIVY_TEMP_LOCK); \
		else \
			echo "WARNING: Environment '$${env}' does not exist locally. Skipping."; \
		fi; \
	done
	@if [ ! -s "$(TRIVY_TEMP_LOCK)" ]; then \
		echo "ERROR: $(TRIVY_TEMP_LOCK) is empty! No dependencies were frozen."; \
		exit 1; \
	fi
	@echo "--- Aggregated Dependencies ---"
	@cat $(TRIVY_TEMP_LOCK)
	@echo "-------------------------------"
	@echo "Running Trivy filesystem scan on $(PROJECT_ROOT)..."
	trivy fs \
		--include-dev-deps \
		--severity $(TRIVY_SEVERITY) \
		--format table \
		--file-patterns pip:$(TRIVY_TEMP_LOCK) \
		$(PROJECT_ROOT)
	@rm -f $(TRIVY_TEMP_LOCK)

