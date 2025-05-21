# Secure Communication with Trusted Execution Environment (TEE) Tutorial (Multi-Step Extension)

This tutorial builds on the tee-client tutorial. Here, you'll implement a multi-step, multi-query chat method that orchestrates several TEE queries and external tool calls to answer complex questions. All other parts of the client (attestation, key management, signature verification, etc.) are assumed to be already implemented as in the tee-client tutorial.

## Prerequisites

- You have completed the tee-client tutorial and have a working TEE client with attestation, encryption, and signature verification.
- You are working in the `coin-price-bot/local/workspace` directory.

## Project Structure

- `client.py`: Contains your `ClientRequest` class. Only the `chat` method needs to be implemented for this tutorial.
- `util/`: Directory containing helper utilities (`signer.py`, `verifier.py`, `root.pem`).
- `requirements.txt`: Lists the required dependencies.

## Goal

You will implement a `chat` method that:
1. Asks the TEE for URLs that can answer the user's question.
2. Extracts URLs from the TEE's response.
3. Fetches the content of each URL.
4. Summarizes each URL's content by sending it to the TEE.
5. Synthesizes a final answer by sending all summaries to the TEE.

## Step-by-Step Implementation: Multi-Step `chat` Method

### 1. Add Helper Methods (if not already present)

Add these to your `ClientRequest` class if you haven't already:

```python
import re

def extract_urls(self, text):
    url_pattern = r'https?://[^\s,]+'
    return re.findall(url_pattern, text)

def fetch_url_content(self, url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""
```

### 2. Implement the Multi-Step `chat` Method

Replace your old `chat` method with the following, which performs the following steps:
1. **Ask the TEE for URLs** that can help answer the user's question.
2. **Extract URLs** from the TEE's response.
3. **Fetch the content** of each URL.
4. **Summarize each URL's content** by sending it (with the original question) to the TEE.
5. **Synthesize a final answer** by sending all summaries to the TEE for a final response.

```python
def chat(self, message: str):
    # 1. Ask TEE for URLs that can answer the user's prompt
    url_prompt = (
        f"List 5 exact URLs (no explanations, just the URLs, one per line) "
        f"that would help answer the following question:\n\n{message}\n"
    )
    data = {
        "api_key": self.api_key,
        "message": url_prompt,
        "platform": self.platform,
        "ai_model": self.model,
    }
    nonce = os.urandom(32)
    req = {
        "nonce": nonce.hex(),
        "public_key": self.signer.get_public_key_der().hex(),
        "data": self.signer.encrypt(bytes.fromhex(self.public_key), nonce, json.dumps(data).encode()).hex()
    }
    url_resp = requests.post(f"{self.tee_endpoint}/talk", json=req).json()
    print("\nStep 1: URL response:", url_resp)
    url_text = url_resp["data"]["response"]
    urls = self.extract_urls(url_text)
    print("Extracted URLs:", urls)

    # 2. Fetch content for each URL
    url_contents = {}
    for url in urls:
        print(f"\nFetching content for: {url}")
        url_contents[url] = self.fetch_url_content(url)

    # 3. Summarize each URL's content via TEE
    summaries = {}
    for url, content in url_contents.items():
        if not content.strip():
            summaries[url] = "[No content fetched]"
            continue
        summary_prompt = (
            f"Given the original question:\n{message}\n\n"
            f"Summarize the following content from {url} in a way that is relevant to the question:\n\n{content[:10000]}"
        )
        data = {
            "api_key": self.api_key,
            "message": summary_prompt,
            "platform": self.platform,
            "ai_model": self.model,
        }
        nonce = os.urandom(32)
        req = {
            "nonce": nonce.hex(),
            "public_key": self.signer.get_public_key_der().hex(),
            "data": self.signer.encrypt(bytes.fromhex(self.public_key), nonce, json.dumps(data).encode()).hex()
        }
        summary_resp = requests.post(f"{self.tee_endpoint}/talk", json=req).json()
        print(f"\nSummary for {url}:", summary_resp)
        summaries[url] = summary_resp["data"]["response"]

    # 4. Final summary: ask TEE to synthesize all summaries into a final answer
    combined_summaries = "\n\n".join(
        f"URL: {url}\nSummary: {summary}" for url, summary in summaries.items()
    )
    final_prompt = (
        f"Given the original question:\n{message}\n\n"
        f"and the following summaries from various sources:\n\n{combined_summaries}\n\n"
        f"Provide a concise, well-sourced answer to the original question."
    )
    data = {
        "api_key": self.api_key,
        "message": final_prompt,
        "platform": self.platform,
        "ai_model": self.model,
    }
    nonce = os.urandom(32)
    req = {
        "nonce": nonce.hex(),
        "public_key": self.signer.get_public_key_der().hex(),
        "data": self.signer.encrypt(bytes.fromhex(self.public_key), nonce, json.dumps(data).encode()).hex()
    }
    final_resp = requests.post(f"{self.tee_endpoint}/talk", json=req).json()
    print("\nFinal synthesized answer:", final_resp["data"]["response"])
    print("verify signature:", self.verify_sig(final_resp["data"], final_resp["sig"]))

    return final_resp["data"]["response"]
```

---

**Note:**
This approach is very naive and mainly for demonstration. It does not handle errors robustly, does not parallelize requests, and is not modular. In future tutorials, we will explore more structured and robust ways to build multi-step, tool-using AI clients.

## Understanding the Flow

1. **Attestation Verification**: The client verifies the TEE's identity.
2. **Secure Communication**: Messages are encrypted for the TEE, and TEE responses are signed.

## Testing Your Implementation

After implementing all the methods in `coin-price-bot/local/workspace/client.py`, you can test it by running:

```bash
python main.py 
```

## Conclusion

This tutorial guided you through implementing a secure TEE client. This ensures sensitive data (like API keys or prompts) is protected during communication with a TEE.