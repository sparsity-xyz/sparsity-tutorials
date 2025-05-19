run-host:
	PYTHONPATH="$$PYTHONPATH:$$PWD" python3 host/main.py

build-tee-tee-tls:
	docker build -t tee-tee-tls .

run-tee-tee-tls-local: build-tee-tee-tls
	docker run -ti --rm -p 9982:9982 --add-host=host.docker.internal:host-gateway -e LOCAL=true tee-tee-tls