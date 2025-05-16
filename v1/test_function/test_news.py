from alpaca_trade_api import REST
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time
import json

API_KEY = "PKKZPSO1JRXTAPX5CS77"
API_SECRET = "8zbSnBa4DMs1hViup4VIzYYCcAEJcUAzZPQtgYB7"
BASE_URL = "https://paper-api.alpaca.markets/v2"
api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)


today = datetime(2024, 5, 16)

# Increase dates
three_days_prior = today - timedelta(days=3)
today = today.strftime("%Y-%m-%d")
three_days_prior = three_days_prior.strftime("%Y-%m-%d")

news = api.get_news(
    symbol=f"BTC/USD", start=three_days_prior, end=today
)

# Extract URLs
news_urls = [ev.__dict__["_raw"]["url"] for ev in news]

# print("Found URLs:")
# for url in news_urls:
#     print(url)

# Function to extract Benzinga article content


def get_benzinga_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    article_json = None
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'NewsArticle':
                article_json = data
                break
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') == 'NewsArticle':
                        article_json = item
                        break
        except:
            continue

    if article_json and 'articleBody' in article_json:
        return article_json['articleBody']

    # Method 1: Try to get article content directly
    article_content = soup.select_one('.article-content-body')
    if article_content:
        paragraphs = article_content.find_all('p')
        if paragraphs:
            return '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

    # Method 2: Look for specific content containers
    content_div = soup.select_one('.content-article, .article-body-content, .article-content')
    if content_div:
        paragraphs = content_div.find_all('p')
        if paragraphs:
            return '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

    # Method 3: Try another common container format
    content_body = soup.find('div', class_=lambda x: x and ('content' in x or 'article' in x))
    if content_body:
        paragraphs = content_body.find_all('p')
        if paragraphs:
            return '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

    # If we can't find structured content, try the meta description at least
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return "META DESCRIPTION ONLY: " + meta_desc.get('content')

    return "Could not extract article content"



# Get content for each URL
print("\nFetching article content:")
for i, url in enumerate(news_urls[:3]):
    print(f"\n--- Article {i+1} ---")
    print(f"URL: {url}")
    content = get_benzinga_content(url)

    # Print content with better formatting
    print("\nARTICLE CONTENT:")
    print("-" * 80)
    print(content[:1500] + ("..." if len(content) > 1500 else ""))
    print("-" * 80)

    # Add a small delay between requests
    if i < len(news_urls[:3]) - 1:
        time.sleep(2)
