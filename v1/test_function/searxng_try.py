import requests
import json
from datetime import datetime


def get_btc_latest_news(query):
    """Get the latest news about Bitcoin from SearXNG"""

    # Parameters to focus on news and recency
    params = {
        'q': query,  # Search query
        'format': 'json',         # Get JSON response
        'categories': 'news',     # Focus on news category
        'time_range': 'day',      # Get recent news (options: day, week, month, year)
        'engines': 'google_news,bing_news,brave,duckduckgo',  # Use news-focused engines
        'language': 'en'          # English results
    }

    response = requests.get('http://localhost:8080/search', params=params)
    data = response.json()

    # Format the results for easier consumption
    news_articles = []
    for result in data.get('results', []):
        article = {
            'title': result.get('title', ''),
            'url': result.get('url', ''),
            'content': result.get('content', ''),
            'source': result.get('engine', ''),
            'publishedDate': result.get('publishedDate', '')
        }
        news_articles.append(article)

    # Sort by most recent (if publishedDate is available)
    # Use a default string that will sort correctly when publishedDate is missing
    news_articles.sort(key=lambda x: x.get('publishedDate') or '', reverse=True)

    return {
        'timestamp': datetime.now().isoformat(),
        'total_results': len(news_articles),
        'articles': news_articles
    }


# Get and print the latest BTC news
btc_news = get_btc_latest_news(query="Bitcoin BTC news")
print(f"Found {btc_news['total_results']} news articles about Bitcoin")

# Print the first 5 news headlines
for i, article in enumerate(btc_news['articles'][:5], 1):
    print(f"\n{i}. {article['title']}")
    print(f"   Source: {article['source']}")
    print(f"   URL: {article['url']}")
    print(f"   Summary: {article['content'][:150]}..." if article['content'] else "   [No summary available]")
    print(f"   Published Date: {article['publishedDate']}")
