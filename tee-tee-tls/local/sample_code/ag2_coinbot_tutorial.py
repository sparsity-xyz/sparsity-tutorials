import os
import openai
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import tiktoken
from typing import Dict, List, Optional

# Load environment variables from .env file
load_dotenv()

# Step a: Get a user prompt (will be implemented later in main())


# Step b: Generate prompt to get URLs using LLM
def generate_search_urls(user_prompt: str, model: str = "gpt-4o") -> List[str]:
    """
    Use an LLM to generate a list of URLs relevant to the user prompt.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = (
        "List me all the URLs you need to search for to get a result for the following prompt: "
        f"{user_prompt}\n"
        "Return only the URLs, one per line, no explanations. "
        "Do not include any other text in your response, and the URLs should be very specific "
        "to cryptocurrency and financial information that can actually solve the user prompt."
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that knows how to find cryptocurrency information on the web."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract URLs from the response
    urls_text = response.choices[0].message.content
    return extract_urls(urls_text)


# Step c: Get URL website data
def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text using regex.
    """
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(text)


def clean_html(html: str) -> str:
    """
    Remove scripts, styles, noscript, and comments, but keep semantic tags.
    """
    soup = BeautifulSoup(html, 'html.parser')
    # Remove unwanted tags
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    
    # Return main content
    main_content = soup.find('main') or soup.find('article') or soup.body
    return str(main_content) if main_content else str(soup)


def fetch_html(url: str) -> str:
    """
    Fetch and process HTML content from a URL.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text
        processed_html = clean_html(html_content)
        
        # Token count comparison
        try:
            enc = tiktoken.encoding_for_model("gpt-4o")
            orig_tokens = len(enc.encode(html_content))
            proc_tokens = len(enc.encode(processed_html))
            reduction = 100 * (orig_tokens - proc_tokens) / max(orig_tokens, 1)
            print(f"Token count for {url}: Original={orig_tokens}, Processed={proc_tokens}, Reduction={reduction:.1f}%")
        except Exception as e:
            print(f"Error calculating tokens: {e}")
        
        return processed_html
    except Exception as e:
        error_msg = f"[ERROR] Could not fetch HTML: {e}"
        print(f"  {error_msg}")
        return error_msg


# Step d: Summarize individual sources using LLM
def summarize_source(html: str, user_prompt: str, model: str = "gpt-4o") -> str:
    """
    Summarize content from a single source based on the user prompt.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Truncate HTML if needed to fit context window
    truncated_html = html[:12000]  # Approximate limit to avoid exceeding context window
    
    prompt = (
        f"Given the following HTML content from a cryptocurrency website, answer the user prompt: '{user_prompt}'. "
        "Focus on extracting relevant cryptocurrency information, prices, trends, or metrics. "
        "If the content is not useful, say so.\n\n"
        f"{truncated_html}"
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a cryptocurrency research assistant that can analyze and summarize web content."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content


# Step e: Summarize and return the final result using LLM
def create_final_summary(source_summaries: Dict[str, str], user_prompt: str, model: str = "gpt-4o") -> str:
    """
    Create a final summary from all source summaries.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Format all source summaries
    formatted = ""
    for i, (url, summary) in enumerate(source_summaries.items(), 1):
        formatted += f"Source {i}: {url}\n{summary}\n\n"
    
    prompt = (
        f"Based on the following cryptocurrency research information from several sources, create a comprehensive answer to the user's question: '{user_prompt}'. "
        "Provide specific details about prices, trends, or metrics mentioned. "
        "Format your response as a clear, concise report with bullet points for key insights.\n\n"
        f"{formatted}"
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a cryptocurrency analyst that creates concise, informative summaries from research data."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content


def main():
    print("AG2 Coinbot: Cryptocurrency Research Assistant")
    print("------------------------------------------")
    print("Type 'exit' to quit\n")
    
    # Step a: Get a user prompt
    while True:
        user_input = input("What cryptocurrency information would you like to research? ")
        if user_input.lower() == 'exit':
            break
        
        # Step b: Generate URLs
        print("\n[Step 1] Generating relevant cryptocurrency research URLs...")
        urls = generate_search_urls(user_input)
        
        if not urls:
            print("No URLs found. Try rephrasing your query with more specific cryptocurrency terms.")
            continue
        
        print(f"Found {len(urls)} relevant sources to research.")
        
        # Step c: Fetch HTML
        url_html_dict = {}
        for url in urls[:3]:  # Limit to 3 URLs to avoid overwhelming
            print(f"\n[Step 2] Fetching content from: {url}")
            html = fetch_html(url)
            url_html_dict[url] = html
        
        # Step d: Summarize individual sources
        print("\n[Step 3] Analyzing content from each source...")
        source_summaries = {}
        for url, html in url_html_dict.items():
            print(f"Analyzing: {url}")
            summary = summarize_source(html, user_input)
            source_summaries[url] = summary
            print(f"Analysis complete for: {url}")
        
        # Step e: Create final summary
        print("\n[Step 4] Creating comprehensive cryptocurrency analysis...")
        final_summary = create_final_summary(source_summaries, user_input)
        
        print(f"\n[Final Cryptocurrency Analysis]\n{final_summary}\n")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key in a .env file or directly in the environment.")
        exit(1)
    main() 