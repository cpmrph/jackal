.PHONY: run
run:
	poetry run python main.py

.PHONY: fmt
fmt:
	poetry run python -m black .
