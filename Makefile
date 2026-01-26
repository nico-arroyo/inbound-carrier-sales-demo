SHELL := /bin/bash

APP_NAME := inbound-carrier-sales-poc
COMPOSE := docker compose

.PHONY: help up down logs build rebuild restart ps sh test curl-health curl-search fmt

help:
	@echo ""
	@echo "Targets:"
	@echo "  make up           Build and run the API"
	@echo "  make down         Stop and remove containers"
	@echo "  make logs         Follow logs"
	@echo "  make build        Build image"
	@echo "  make rebuild      Rebuild without cache"
	@echo "  make restart      Restart service"
	@echo "  make ps           Show running containers"
	@echo "  make sh           Shell into api container"
	@echo "  make curl-health  Hit /health"
	@echo "  make curl-search  Example /v1/loads/search request"
	@echo ""

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) build --no-cache

restart:
	$(COMPOSE) restart api

ps:
	$(COMPOSE) ps

sh:
	$(COMPOSE) exec api sh

curl-health:
	curl -s http://localhost:8000/health | python -m json.tool

curl-search:
	curl -s -X POST http://localhost:8000/v1/loads/search \
	  -H "Content-Type: application/json" \
	  -H "X-API-Key: $${API_KEY:-demo-key}" \
	  -d '{"origin":"Atlanta, GA","destination":"Dallas, TX","equipment_type":"dry_van","limit":5}' \
	| python -m json.tool
