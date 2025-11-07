.PHONY: setup install test run clean help

# Default target
help:
	@echo "SMS News Service - Available Commands"
	@echo ""
	@echo "  make setup      - Create venv and install dependencies"
	@echo "  make test       - Run in test mode (no real SMS sent)"
	@echo "  make run        - Run in production mode (sends real SMS)"
	@echo "  make clean      - Remove venv and generated files"
	@echo "  make install    - Install additional dependencies"
	@echo "  make help       - Show this help message"
	@echo ""

# Setup virtual environment and install dependencies
setup:
	@echo "Setting up SMS News Service..."
	@./setup.sh

# Install dependencies (for updating packages)
install:
	@echo "Installing/updating dependencies..."
	@./venv/bin/pip install -r requirements.txt

# Run in test mode
test:
	@echo "Running in test mode (dry-run)..."
	@./run.sh --test

# Run in production mode
run:
	@echo "Running in production mode..."
	@./run.sh

# Clean up generated files
clean:
	@echo "Cleaning up..."
	@rm -rf venv/
	@rm -rf __pycache__/
	@rm -rf news_aggregator/__pycache__/
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@echo "Clean complete. Run 'make setup' to reinstall."
