import re

import requests
from bs4 import BeautifulSoup, Comment
from util.log import logger


def url_prompt(user_prompt: str) -> str:
    return (
        "List me all the URLs you need to search for to get a result for the following prompt: "
        f"{user_prompt}\n"
        "Return only the URLs, one per line, no explanations. "
        "Do not include any other text in your response, and the URL should be very very specific so it can actually solve the user prompt."
        "Do not say you can't provide any URLs, just return the URLs you can find."
        "I will do visit the websites myself, so just give me the URLS. NEVER say you can't provide any URLs."
    )


def summary_prompt(user_prompt: str, url: str, html: str) -> str:
    return (
        f"Summarize the following HTML content from {url} regarding the user prompt: '{user_prompt}'. "
        "If the content is not useful, say so.\n\n" + html[:10000]
    )


def final_summary_prompt(user_prompt: str, url_summaries: str) -> str:
    return (
        f"Given the following summaries of content from several URLs, use the information to answer the user prompt: '{user_prompt}'. "
        "If the content is not useful, say so.\n\n" + url_summaries
    )


def extract_urls(text: str) -> list[str]:
    # Simple regex to extract URLs from text
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(text)


def custom_get(url):
    try:
        return requests.get(url, verify="/usr/local/share/ca-certificates/Certificate.crt").json()
    except Exception as e:
        logger.error(f"Failed to get {url}: {e}")
        return None


def custom_post(url, data):
    try:
        return requests.post(url, json=data, verify="/usr/local/share/ca-certificates/Certificate.crt").json()
    except Exception as e:
        logger.error(f"Failed to post {url}: {e}")
        return None


def clean_html(html: str) -> str:
    """
    Remove scripts, styles, noscript, and comments, but keep semantic tags (h1, table, ul, etc).
    Returns the main content (main, article, or body).
    """
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    # Return main content
    return str(soup.find('main') or soup.find('article') or soup.body)


def fetch_html(url):
    # Fetch the raw HTML from the URL and process it
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text
        processed_html = clean_html(html_content)
        return processed_html
    except Exception as e:
        error_msg = f"[ERROR] Could not fetch HTML: {e}"
        print(f"  {error_msg}")
        return error_msg
