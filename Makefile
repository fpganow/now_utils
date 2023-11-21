
.PHONY: test
test:
	. ./venv_wsl/bin/activate && python3.11 -m pytest --log-cli-level ERROR tests/

