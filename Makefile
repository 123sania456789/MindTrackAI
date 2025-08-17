.PHONY: help install run test clean docker-up docker-down docker-build logs

help: ## Show this help message
	@echo "MindTrack AI - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm
	python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

run: ## Run the Flask application locally
	python start.py

test: ## Run tests (placeholder)
	@echo "Tests not implemented yet"

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete

docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-build: ## Build Docker images
	docker-compose build

docker-logs: ## View Docker logs
	docker-compose logs -f

logs: ## View application logs
	tail -f logs/mindtrack_ai.log

setup: ## Initial setup for development
	@echo "Setting up MindTrack AI development environment..."
	@echo "1. Installing dependencies..."
	$(MAKE) install
	@echo "2. Creating necessary directories..."
	mkdir -p logs models
	@echo "3. Setting up environment file..."
	@if [ ! -f .env ]; then \
		cp env_example.txt .env; \
		echo "Created .env file from env_example.txt"; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi
	@echo "4. Setup complete!"
	@echo "Next steps:"
	@echo "  - Edit .env file with your configuration"
	@echo "  - Start PostgreSQL and Redis services"
	@echo "  - Run 'make run' to start the application"

dev: ## Start development environment
	@echo "Starting development environment..."
	@echo "Make sure PostgreSQL and Redis are running!"
	$(MAKE) run

prod: ## Start production environment with Docker
	@echo "Starting production environment..."
	$(MAKE) docker-build
	$(MAKE) docker-up

status: ## Check service status
	@echo "Checking service status..."
	@docker-compose ps
	@echo ""
	@echo "Database connection:"
	@python -c "from app import app, db; app.app_context().push(); print('✅ Database accessible' if db.engine.execute('SELECT 1') else '❌ Database error')" 2>/dev/null || echo "❌ Database not accessible"
	@echo ""
	@echo "Redis connection:"
	@python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print('✅ Redis accessible' if r.ping() else '❌ Redis error')" 2>/dev/null || echo "❌ Redis not accessible"

reset: ## Reset database and start fresh
	@echo "⚠️  This will delete all data! Are you sure? [y/N]"
	@read -p "" confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "Resetting database..."; \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		$(MAKE) run; \
	else \
		echo "Reset cancelled"; \
	fi


