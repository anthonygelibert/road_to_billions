ifndef VIRTUAL_ENV
$(error This project should be made from a venv... You are ruining your system son...)
endif

.PHONY: help check

# COLORS
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)
# MAX SIZE OF A TARGET NAME
TARGET_MAX_CHAR_NUM=15

help: ## Show help
	@echo '${WHITE}Usage:${RESET}'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo '${WHITE}Targets:${RESET}'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; { \
				printf "  ${YELLOW}%-$(TARGET_MAX_CHAR_NUM)s${RESET} ${GREEN}%s${RESET}\n", $$1, $$2 \
			}'

check: ## Code checking with ruff
	ruff check --config ruff.toml wayne

# Pro tip: during usual calls silent everything and if V="SOMETHING" be verbose
$(V).SILENT:
