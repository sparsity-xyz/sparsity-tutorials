run-host:
	PYTHONPATH="$$PYTHONPATH:$$PWD" python3 host/main.py

build-ag2-mcp:
	docker build -t tee-ag2-mcp .

run-ag2-mcp-local: build-ag2-mcp
	docker run -ti --rm -p 9982:9982 --add-host=host.docker.internal:host-gateway -e LOCAL=true tee-ag2-mcp