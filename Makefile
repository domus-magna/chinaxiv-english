PY?=$(shell command -v python3.11 2>/dev/null || command -v python3 2>/dev/null || echo python)
PORT?=8001
VENV=.venv
VPY=$(VENV)/bin/python
VPIP=$(VENV)/bin/pip
DEV_LIMIT?=5
MODEL?=

.PHONY: setup test lint fmt smoke build serve health clean samples

setup:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

venv:
	$(PY) -m venv $(VENV)
	$(VPY) -m pip install --upgrade pip
	$(VPIP) install -r requirements.txt

test:
	$(PY) -m pytest -q

lint:
	ruff check src tests

fmt:
	black src tests

health:
	$(PY) -m src.health --skip-openrouter || true

smoke:
	$(PY) -m src.harvest_oai || true
	@latest=$$(ls -1t data/records/*.json 2>/dev/null | head -n1 || echo ''); \
	if [ -n "$$latest" ]; then \
		$(PY) -m src.select_and_fetch --records "$$latest" --limit 2 --output data/selected.json || true; \
	else \
		echo '[]' > data/selected.json; \
	fi
	$(PY) -m src.translate --selected data/selected.json --dry-run
	$(PY) -m src.render
	$(PY) -m src.search_index
	$(PY) -m src.make_pdf || true

build: smoke

serve:
	$(PY) -m http.server -d site $(PORT)

samples:
	@echo "Generating before/after samples into site/samples/ ..."
	$(PY) -m src.tools.formatting_compare --count 3 || true
	@echo "Open http://localhost:$(PORT)/samples/ after running 'make serve'"

clean:
	rm -rf site data

dev: clean venv
	@if [ -z "$$OPENROUTER_API_KEY" ] && [ ! -f .env ]; then echo "Set OPENROUTER_API_KEY or create .env"; exit 1; fi
	$(VPY) -m pytest -q
	# Proceed even if OAI is unreachable locally; OpenRouter must be OK
	$(VPY) -m src.health --skip-oai || true
	$(VPY) -m src.harvest_oai || true
	@latest=$$(ls -1t data/records/*.json 2>/dev/null | head -n1 || echo ''); \
	if [ -n "$$latest" ]; then \
		$(VPY) -m src.select_and_fetch --records "$$latest" --limit $(DEV_LIMIT) --output data/selected.json || true; \
	else \
		echo '[]' > data/selected.json; \
	fi
	@if [ ! -s data/selected.json ] || [ "$$($(VPY) -c 'import json,sys;print(json.load(open("data/selected.json"))==[])' )" = "True" ]; then \
		echo 'Seeding sample record for dev...'; \
		mkdir -p data; \
		echo '[{"id":"dev-1","oai_identifier":"oai:chinaxiv.org:dev-1","title":"Test title","abstract":"This is a test abstract with formula $E=mc^2$.","creators":["Li, Hua"],"subjects":["cs.AI"],"date":"2025-10-03","source_url":"https://example.org/","license":{"raw":"CC BY"}}]' > data/selected.json; \
	fi
	# Translate (allow model override; fallback to dry-run on failure)
	$(VPY) -m src.translate --selected data/selected.json $(if $(MODEL),--model $(MODEL),) \
	|| (echo 'Translation failed; falling back to --dry-run' && $(VPY) -m src.translate --selected data/selected.json --dry-run)
	$(VPY) -m src.render
	$(VPY) -m src.search_index
	-$(VPY) -m src.make_pdf
	@echo "Starting server at http://localhost:$(PORT) (Ctrl+C to stop)"
	$(VPY) -m http.server -d site $(PORT)
