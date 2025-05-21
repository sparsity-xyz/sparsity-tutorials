run-host:
	PYTHONPATH="$$PYTHONPATH:$$PWD" python3 host/main.py

build-price-bot:
	docker build -t price-bot .

run-price-bot-local: build-price-bot
	docker run -ti --rm -p 9982:9982 --add-host=host.docker.internal:host-gateway -e LOCAL=true price-bot