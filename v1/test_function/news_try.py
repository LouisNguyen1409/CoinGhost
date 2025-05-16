from gnews import GNews
from googlenewsdecoder import gnewsdecoder
from datetime import datetime, timedelta
import random
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json


def fetch_bitcoin_articles(start, end):
    gn = GNews(language='en')
    delta = timedelta(days=1)
    items = []
    while start < end:
        chunk_end = min(start + delta, end)
        items.append(
            gn.get_news(f"Bitcoin BTC news after:{start:%Y-%m-%d} before:{chunk_end:%Y-%m-%d}")
        )
        start = chunk_end + timedelta(days=1)

    print(items)
    return items


def extract_article_content(url):
    """Extract article content using BeautifulSoup."""
    # List of common user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
    ]

    user_agent = random.choice(user_agents)
    domain = urlparse(url).netloc

    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': f'https://www.google.com/search?q={domain}',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

    # Create a dict to store article data
    article_data = {
        'url': url,
        'title': '',
        'text': '',
        'publish_date': None
    }

    try:
        # Simple retry mechanism (maximum 2 attempts)
        for attempt in range(2):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                break
            except:
                if attempt == 1:  # Last attempt failed
                    return None
                time.sleep(3)  # Wait before retry
                continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to extract title from page
        title = soup.find('title')
        if title:
            article_data['title'] = title.get_text().strip()

        # Try to find publication date
        # Common date meta tags
        date_meta_tags = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publication_date'}),
            ('meta', {'name': 'date'}),
            ('meta', {'property': 'og:published_time'}),
            ('meta', {'itemprop': 'datePublished'}),
            ('time', {})
        ]

        for tag, attrs in date_meta_tags:
            date_element = soup.find(tag, attrs)
            if date_element:
                if tag == 'time':
                    date_str = date_element.get('datetime') or date_element.text
                else:
                    date_str = date_element.get('content')

                if date_str:
                    article_data['publish_date'] = date_str
                    break

        # Method 1: Try to extract from JSON-LD
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

        if article_json:
            if 'articleBody' in article_json:
                article_data['text'] = article_json['articleBody']
            if 'headline' in article_json:
                article_data['title'] = article_json['headline']
            if 'datePublished' in article_json:
                article_data['publish_date'] = article_json['datePublished']

            if article_data['text']:
                return article_data

        # Method 2: Try common article selectors
        common_article_selectors = [
            '.article-content-body', '.content-article', '.article-body-content',
            '.article-content', '.article__body', '.article-body',
            '.post-content', '.entry-content', '.content-body',
            'article', 'main'
        ]

        for selector in common_article_selectors:
            article_content = soup.select_one(selector)
            if article_content:
                paragraphs = article_content.find_all('p')
                if paragraphs:
                    article_data['text'] = '\n\n'.join([p.get_text().strip()
                                                       for p in paragraphs if p.get_text().strip()])
                    if article_data['text']:
                        return article_data

        # Method 3: Try another common container format
        for class_keyword in ['content', 'article', 'story', 'entry', 'post', 'text', 'body']:
            content_body = soup.find('div', class_=lambda x: x and (class_keyword in x.lower() if x else False))
            if content_body:
                paragraphs = content_body.find_all('p')
                if paragraphs:
                    article_data['text'] = '\n\n'.join([p.get_text().strip()
                                                       for p in paragraphs if p.get_text().strip()])
                    if article_data['text']:
                        return article_data

        # Method 4: Just grab all paragraphs from the page
        all_paragraphs = soup.find_all('p')
        if all_paragraphs:
            # Filter paragraphs by length to avoid navigation/footer paragraphs
            content_paragraphs = [p for p in all_paragraphs if len(p.get_text().strip()) > 80]
            if content_paragraphs:
                article_data['text'] = '\n\n'.join([p.get_text().strip() for p in content_paragraphs])
                if article_data['text']:
                    return article_data

        # Method 5: Try meta description as last resort
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find(
            'meta', attrs={'property': 'og:description'})
        if meta_desc and meta_desc.get('content'):
            article_data['text'] = meta_desc.get('content')
            return article_data

        return None

    except Exception as e:
        print(f"Error extracting content: {e}")
        return None


def process_article(art):
    raw_url = art['url']

    # Decode the Google News URL
    result = gnewsdecoder(raw_url, interval=1)
    if not result.get("status"):
        print("⚠️ Decode failed:", result.get("message"))
        real_url = raw_url
    else:
        real_url = result["decoded_url"]

    # Extract article content using BeautifulSoup
    article = extract_article_content(real_url)

    # Handle the result
    if article and article['text']:
        print("✅ Title:    ", art.get("title"))
        return article
    else:
        print(f"❌ Error processing article: {art.get('title')}")
        return None


def main():
    start = datetime(2024, 5, 10)
    end = datetime(2024, 5, 11)
    articles = fetch_bitcoin_articles(start, end)
    print("Found", len(articles), "articles")

    # clean_articles = []
    # for art in articles:
    #     article = process_article(art)
    #     if article:
    #         clean_articles.append(article)

    # print("Found", len(clean_articles), "clean articles")

    # for i, article in enumerate(clean_articles):
    #     print(f"{i+1}. Title:    ", article['title'])
    #     print("   URL:      ", article['url'])
    #     print("   Date:     ", article['publish_date'])
    #     print("   Snippet:  ", article['text'][:1500].replace("\n", " "))


if __name__ == "__main__":
    main()
