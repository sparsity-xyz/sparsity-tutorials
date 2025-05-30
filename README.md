# Sparsity Tutorials: Main Guide

Welcome! This repository is a collection of hands-on tutorials to help you learn how the Sparsity infrastructure works and how to build secure, tool-using AI agents on top of it.

---

## ⚙️ Requirements

Before you begin, make sure you have the following:
- **OpenAI API key** (or Gemini API key)
- **Python >= 3.10**
- **Docker**
- **make**
- (optional) **venv** (Python virtual environment)

---

For the python environment, we recommend you to create a python `venv` using the following command and activate it.
```
python -m venv .venv
source .venv/bin/activate
```
This will ensure the installed libraries/packages persist across the tutorial and take care of required libraries once you install them using `pip install`.

Below is the recommended order for working through the tutorials. Each step introduces new features and concepts, and each project has its own detailed `Tutorial.md`.

---

## 📚 Tutorial Index

1. **tee-client**
   - **Learn:** The basics of secure client-server communication using TEE (Trusted Execution Environment) and attestation.
   - **Features:** Simple encrypted chat, attestation verification, basic TEE API usage.
   - **Start here:** [`tee-client/Tutorial.md`](tee-client/Tutorial.md)

2. **coin-price-bot/local**
   - **Learn:** How to build a local tool-using AI agent that can fetch and summarize real-world data (e.g., coin prices) using external APIs.
   - **Features:** Tool-using agent, API integration, prompt engineering, local development.
   - **Go to:** [`coin-price-bot/local/Tutorial.md`](coin-price-bot/local/Tutorial.md)

3. **agent-mcp/local**
   - **Learn:** How to build a more advanced, modular tool-using agent with multi-step reasoning and tool invocation.
   - **Features:** Modular agent design, multi-step tool use, advanced prompt workflows.
   - **Go to:** [`agent-mcp/local/Tutorial.md`](agent-mcp/local/Tutorial.md)

4. **coin-price-bot/sim-tee**
   - **Learn:** How to deploy the coin-price-bot agent inside a simulated TEE, with secure proxying, DNS routing, and multi-step retrieval-augmented generation (RAG).
   - **Features:** TEE simulation, secure proxy, DNS interception, multi-step RAG agent, containerized deployment.
   - **Go to:** [`coin-price-bot/sim-tee/Tutorial.md`](coin-price-bot/sim-tee/Tutorial.md)

5. **agent-mcp/sim-tee**
   - **Learn:** How to deploy a modular, multi-tool agent inside a simulated TEE, with secure attestation, toolkits, and advanced agent orchestration.
   - **Features:** Secure TEE agent, attestation, toolkits, multi-step orchestration, containerized deployment.
   - **Go to:** [`agent-mcp/sim-tee/Tutorial.md`](agent-mcp/sim-tee/Tutorial.md)

---

## How to Use This Guide
- Work through the tutorials in order for the best learning experience.
- Each tutorial builds on the previous one, introducing new infrastructure, security, and agent features.
- For each project, follow the instructions in its `Tutorial.md`.

Happy hacking!
