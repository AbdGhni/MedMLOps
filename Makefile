.PHONY: core-test core-pipeline core-validate
core-test:
	python -m unittest discover -s tests -v
core-pipeline:
	python -m medmlops.pipeline all
core-validate:
	python -m scripts.validate_v2
