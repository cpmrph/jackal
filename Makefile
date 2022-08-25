USER=

.PHONY: run
run:
	poetry run python -m jackal $(USER)

.PHONY: fmt
fmt:
	poetry run python -m black jackal
