.PHONY: help build-all build-internal build-client serve-internal serve-client

help:
	@echo "Commandes disponibles pour la documentation RTMS :"
	@echo "  make build-all       : Compile les deux documentations (Interne 3TS & Client)"
	@echo "  make build-internal  : Compile le portail technique interne (site-internal/)"
	@echo "  make build-client    : Compile le guide utilisateur client (site-client/)"
	@echo "  make serve-internal  : Lance le serveur local interne sur http://127.0.0.1:8008"
	@echo "  make serve-client    : Lance le serveur local client sur http://127.0.0.1:8009"

build-all: build-internal build-client

build-internal:
	uv run mkdocs build -f mkdocs.internal.yml --strict

build-client:
	uv run mkdocs build -f mkdocs.client.yml --strict

serve-internal:
	uv run mkdocs serve -f mkdocs.internal.yml

serve-client:
	uv run mkdocs serve -f mkdocs.client.yml
