# Top-level entry points for the CS340 reproduction.
# The measured code still lives in TEST_DIR/ and is unchanged.

.PHONY: build bench summarize verify test

build:
	$(MAKE) -C TEST_DIR

# Three full passes on the kernel that is booted now.
# Must be run on Linux. See README.md for runtime and privileges.
bench: build
	python3 scripts/run_current_kernel.py --runs 3

summarize:
	python3 scripts/summarize_runs.py results

# Recompute every published number from results/ and fail on a mismatch.
verify:
	python3 scripts/verify_report_numbers.py

# Unit and integration tests (pure Python, no VM required).
test:
	python3 -m unittest discover -s tests -v
