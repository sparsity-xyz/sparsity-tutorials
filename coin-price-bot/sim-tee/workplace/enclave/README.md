# TEE-TEE-TLS demo

This is a simple python-based agent that requests another TEE endpoint that serves LLM API requests. All responses from the LLM TEE endpoint is verified through signature.

You can change the LLM TEE endpoint with the environment variable `SPARSITY_ENDPOINT`

To build:
```
make build-agent
```

To run locally:
```
make run-agent-local
```