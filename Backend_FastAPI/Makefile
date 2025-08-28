# Makefile for Lexa AI Backend
# Comprehensive development and deployment commands

.PHONY: help install dev serve test migrate rollback clean status backup logs

# Default target
help: ## Show this help message
	@echo "🚀 Lexa AI Backend - Development Commands"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Environment variables:"
	@echo "  ADMIN_PASSWORD    Admin password (default: from .env)"
	@echo "  OPENAI_API_KEY    OpenAI API key (required)"
	@echo "  PORT              Server port (default: 8000)"

# Installation and setup
install: ## Install Python dependencies
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

install-dev: ## Install development dependencies
	@echo "📦 Installing dev dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio httpx black isort flake8
	@echo "✅ Dev dependencies installed"

# Environment setup
env-check: ## Check environment variables and configuration
	@echo "🔍 Checking environment..."
	@python -c "import os; print('✅ OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else '❌ MISSING')"
	@python -c "import os; print('✅ ADMIN_PASSWORD:', 'SET' if os.getenv('ADMIN_PASSWORD') else '⚠️  Using default')"
	@python -c "from pathlib import Path; print('✅ Settings:', 'EXISTS' if Path('storage/settings.json').exists() else '⚠️  Will be created')"
	@python -c "from pathlib import Path; print('✅ Database dir:', 'EXISTS' if Path('Database').exists() else '⚠️  Will be created')"

env-setup: env-check ## Setup environment and initialize settings
	@echo "⚙️  Setting up environment..."
	mkdir -p Database storage storage/branding storage/trash chroma_db
	@if [ ! -f "storage/settings.json" ]; then \
		echo "🔧 Running initial migration..."; \
		python migrate_settings.py; \
	fi
	@echo "✅ Environment setup complete"

# Development
dev: env-setup ## Start development server with auto-reload
	@echo "🔥 Starting development server..."
	uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --reload

serve: env-setup ## Start production server
	@echo "🚀 Starting production server..."
	uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

# Testing
test: ## Run endpoint tests
	@echo "🧪 Running endpoint tests..."
	./test_endpoints.sh

test-quick: ## Quick test of key endpoints only
	@echo "⚡ Quick endpoint test..."
	curl -f http://localhost:8000/health || (echo "❌ Server not running" && exit 1)
	curl -f -u admin:${ADMIN_PASSWORD:-Krypt0n!t3} http://localhost:8000/admin/settings/ai > /dev/null
	@echo "✅ Quick test passed"

test-openai: ## Test OpenAI API connection
	@echo "🤖 Testing OpenAI connection..."
	python test_openai.py

lint: ## Run code linting
	@echo "🔍 Running linters..."
	flake8 --max-line-length=120 --ignore=E501,W503 *.py
	@echo "✅ Linting complete"

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black --line-length=120 *.py
	isort *.py
	@echo "✅ Code formatted"

# Settings management
migrate: ## Run settings migration (add missing fields)
	@echo "🔄 Running settings migration..."
	python migrate_settings.py

rollback: ## Interactive rollback to previous settings
	@echo "⏪ Starting interactive rollback..."
	python rollback_settings.py --list
	@read -p "Enter backup number or filename: " backup; \
	python rollback_settings.py --backup "$$backup"

rollback-latest: ## Rollback to most recent backup
	@echo "⏪ Rolling back to latest backup..."
	python rollback_settings.py --latest

backup: ## Create manual backup of current settings
	@echo "💾 Creating manual backup..."
	@timestamp=$$(date +%Y%m%d-%H%M%S); \
	cp storage/settings.json "storage/settings.json.bak.manual-$$timestamp" && \
	echo "✅ Manual backup created: settings.json.bak.manual-$$timestamp"

status: ## Show current system status
	@echo "📊 System Status"
	@echo "================="
	@python -c "import json; from pathlib import Path; s=json.loads(Path('storage/settings.json').read_text()) if Path('storage/settings.json').exists() else {}; print(f'Settings fields: {len(s)}'); print(f'Company: {s.get(\"companyName\", \"Not set\")}'); print(f'Model: {s.get(\"model\", \"Not set\")}'); print(f'Temperature: {s.get(\"temperature\", \"Not set\")}')"
	@echo ""
	@echo "📁 Files:"
	@ls -la Database/ 2>/dev/null | wc -l | xargs -I {} echo "  Documents: {} files"
	@ls -la storage/*.bak.* 2>/dev/null | wc -l | xargs -I {} echo "  Backups: {} files"
	@echo ""
	@echo "🗄️  Database:"
	@du -sh chroma_db/ 2>/dev/null || echo "  ChromaDB: Not initialized"

# Maintenance
clean: ## Clean temporary files and caches
	@echo "🧹 Cleaning temporary files..."
	rm -rf __pycache__/ .pytest_cache/ *.pyc
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-all: clean ## Clean everything including database and settings
	@read -p "⚠️  This will delete database and settings. Continue? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		echo "🗑️  Removing all data..."; \
		rm -rf chroma_db/ storage/ Database/; \
		echo "✅ All data removed"; \
	else \
		echo "🚫 Cancelled"; \
	fi

reset-db: ## Reset only the vector database (keeps documents)
	@read -p "⚠️  This will reset the vector database. Continue? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		echo "🗑️  Resetting vector database..."; \
		rm -rf chroma_db/; \
		echo "🔄 Triggering re-indexing..."; \
		curl -f -u admin:${ADMIN_PASSWORD:-Krypt0n!t3} -X POST http://localhost:8000/api/scan/ || echo "⚠️  Server not running, will re-index on next startup"; \
		echo "✅ Database reset complete"; \
	else \
		echo "🚫 Cancelled"; \
	fi

# Logging and monitoring
logs: ## Show recent application logs (if running with systemd)
	@echo "📋 Recent logs..."
	@if command -v journalctl >/dev/null 2>&1; then \
		journalctl -u lexa-ai --no-pager -n 50; \
	else \
		echo "⚠️  journalctl not available. Check your process manager logs."; \
	fi

logs-follow: ## Follow application logs in real-time
	@echo "📋 Following logs (Ctrl+C to stop)..."
	@if command -v journalctl >/dev/null 2>&1; then \
		journalctl -u lexa-ai -f; \
	else \
		echo "⚠️  journalctl not available. Check your process manager logs."; \
	fi

# Quick commands for common workflows
start: env-setup dev ## Alias for 'make dev'

stop: ## Stop the development server (if running in background)
	@echo "🛑 Stopping server..."
	@pkill -f "uvicorn app:app" || echo "ℹ️  No server process found"

restart: stop start ## Restart the development server

# CI/CD helpers
ci-test: install test-openai test ## Full CI test suite
	@echo "🎉 All CI tests passed"

deploy-check: env-check lint test-openai ## Pre-deployment checks
	@echo "🔍 Running deployment checks..."
	@python -c "import app; print('✅ App imports successfully')"
	@echo "✅ Deployment checks passed"

# Development shortcuts
shell: ## Start Python shell with app context
	@echo "🐍 Starting Python shell..."
	python -i -c "from app import *; from settings_store import *; print('📱 App context loaded')"

# Information
version: ## Show version information
	@echo "📦 Lexa AI Backend"
	@echo "Version: 2.0.0"
	@echo "FastAPI: $$(python -c 'import fastapi; print(fastapi.__version__)')"
	@echo "Python: $$(python --version)"

docs: ## Show API documentation info
	@echo "📚 API Documentation"
	@echo "===================="
	@echo "OpenAPI/Swagger UI: http://localhost:8000/docs"
	@echo "ReDoc: http://localhost:8000/redoc"
	@echo "OpenAPI JSON: http://localhost:8000/openapi.json"

# Advanced operations
full-reset: backup clean env-setup ## Full system reset with backup
	@echo "🔄 Full system reset complete"

health-check: ## Comprehensive health check
	@echo "🏥 Health Check"
	@echo "==============="
	@make env-check
	@make test-quick
	@make status
	@echo "✅ Health check complete"