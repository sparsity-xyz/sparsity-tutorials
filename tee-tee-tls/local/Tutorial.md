# AG2 Coinbot Tutorial

This tutorial explains the implementation of AG2 Coinbot, a simple agent-based system for cryptocurrency research.

## Overview

AG2 Coinbot follows a multi-step process to research cryptocurrency information:

1. **Get user prompt**: Accept a question or topic about cryptocurrencies from the user
2. **Generate search URLs**: Use LLM to identify relevant websites for research
3. **Retrieve website data**: Fetch and clean HTML content from those websites
4. **Analyze individual sources**: Summarize each source with respect to the user's question
5. **Create comprehensive summary**: Combine all source analyses into a final report

## Step-by-Step Implementation

### Step 1: User Prompt

The workflow begins with the user providing a cryptocurrency-related question or research topic. This happens in the `main()` function where we use `input()` to get the user's query:

```python
user_input = input("What cryptocurrency information would you like to research? ")
```

### Step 2: Generate Search URLs

Next, we use an LLM (GPT-4o in this case) to generate a list of relevant URLs that might contain information to answer the user's query. We implement this in the `generate_search_urls()` function:

```python
def generate_search_urls(user_prompt: str, model: str = "gpt-4o") -> List[str]:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = (
        "List me all the URLs you need to search for to get a result for the following prompt: "
        f"{user_prompt}\n"
        "Return only the URLs, one per line, no explanations. "
        "Do not include any other text in your response, and the URLs should be very specific "
        "to cryptocurrency and financial information that can actually solve the user prompt."
    )
    
    # Call the LLM and extract URLs from response
    ...
```

The prompt instructs the model to return only URLs, one per line, focused specifically on cryptocurrency information sources.

### Step 3: Retrieve Website Data

Once we have the URLs, we need to retrieve and process the HTML content. This involves:

1. **URL extraction**: Using regex to parse URLs from text
2. **HTML fetching**: Making HTTP requests to retrieve raw HTML
3. **HTML cleaning**: Removing unnecessary elements (scripts, styles) to focus on content

Key functions for this step include:

```python
def extract_urls(text: str) -> List[str]:
    """Extract URLs from text using regex."""
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(text)

def clean_html(html: str) -> str:
    """Remove scripts, styles, noscript, and comments, but keep semantic tags."""
    # Use BeautifulSoup to parse and clean HTML
    ...

def fetch_html(url: str) -> str:
    """Fetch and process HTML content from a URL."""
    # Make HTTP request and clean the response
    ...
```

The cleaned HTML is much smaller and more focused on the actual content, which helps improve the quality of the LLM's analysis while reducing token usage.

### Step 4: Analyze Individual Sources

With the HTML content retrieved and cleaned, we analyze each source individually using the LLM. The `summarize_source()` function handles this step:

```python
def summarize_source(html: str, user_prompt: str, model: str = "gpt-4o") -> str:
    """Summarize content from a single source based on the user prompt."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Truncate HTML if needed to fit context window
    truncated_html = html[:12000]
    
    prompt = (
        f"Given the following HTML content from a cryptocurrency website, answer the user prompt: '{user_prompt}'. "
        "Focus on extracting relevant cryptocurrency information, prices, trends, or metrics. "
        "If the content is not useful, say so.\n\n"
        f"{truncated_html}"
    )
    
    # Call LLM to analyze the content
    ...
```

This step creates a separate analysis for each source, focusing specifically on the user's original question.

### Step 5: Create Comprehensive Summary

Finally, we combine all the individual source analyses into a comprehensive final summary using the `create_final_summary()` function:

```python
def create_final_summary(source_summaries: Dict[str, str], user_prompt: str, model: str = "gpt-4o") -> str:
    """Create a final summary from all source summaries."""
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
    
    # Call LLM to create the final summary
    ...
```

This produces a well-structured final report that directly addresses the user's original question.

## Running the Coinbot

To run the AG2 Coinbot:

1. Ensure you have the required dependencies installed:
   ```
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Run the coinbot:
   ```
   python ag2_coinbot_tutorial.py
   ```

4. Enter your cryptocurrency research question when prompted.

## Example Usage

Here's an example of how to use the coinbot:

```
AG2 Coinbot: Cryptocurrency Research Assistant
------------------------------------------
Type 'exit' to quit

What cryptocurrency information would you like to research? What is the current state of Ethereum layer 2 solutions?

[Step 1] Generating relevant cryptocurrency research URLs...
Found 4 relevant sources to research.

[Step 2] Fetching content from: https://ethereum.org/en/layer-2/
Token count for https://ethereum.org/en/layer-2/: Original=45678, Processed=12345, Reduction=73.0%

...

[Final Cryptocurrency Analysis]
- Ethereum layer 2 solutions are scaling technologies built on top of Ethereum that improve transaction throughput and reduce gas fees
- The ecosystem currently has several major players including Optimism, Arbitrum, and zkSync
- Total Value Locked (TVL) across all L2s is approximately $X billion as of [date]
- Recent developments include...
```

## Conclusion

This tutorial has demonstrated how to build a simple but powerful cryptocurrency research assistant using the OpenAI API. The multi-step process allows for targeted information gathering, processing, and synthesis to answer user queries effectively. 