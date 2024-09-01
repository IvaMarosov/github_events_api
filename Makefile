TEST = pytest
TEST_DIR = tests/
TEST_RUN = $(TEST) $(TEST_DIR)

help:
	@echo "make lint"
	@echo "     run complete pre-commit/pre-push lint"
	@echo "make test"
	@echo "     run tests"
	@echo "make check"
	@echo "     run all checks - linting + tests"

lint:
	pre-commit run -a

test:
	$(TEST_RUN)

check: lint test
