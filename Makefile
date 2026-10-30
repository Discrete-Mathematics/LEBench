# Top-level entry points for the CS340 reproduction.
# The measured code still lives in TEST_DIR/ and is unchanged.

.PHONY: build bench summarize

build:
	$(MAKE) -C TEST_DIR

# Three full passes on the kernel that is booted now.
# Must be run on Linux. See README.md for runtime and privileges.
bench: build
	python3 scripts/run_current_kernel.py --runs 3

summarize:
	python3 scripts/summarize_runs.py results
