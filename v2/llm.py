from get_news import google_news, alpaca_news
import re
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from datetime import datetime

load_dotenv()
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY")
LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL")
MODEL = os.getenv("LM_MODEL_NAME")

client = OpenAI(api_key=LMSTUDIO_API_KEY, base_url=LMSTUDIO_API_URL)


def stream_from_lm(model_name: str, prompt: str, temperature=0.7, top_p=0.9):
    """
    Stream chat completions using only user/assistant roles.
    """
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        top_p=top_p,
        stream=True
    )
    return response


def get_recommendation(coin: str, start_date: str, end_date: str, cash: float, btc_quantity: float, get_24h_change: float, get_7d_change: float, get_30d_change: float, last_price: float):
    try:
        alp_news = alpaca_news(coin, start_date, end_date)
        news = alp_news
    except Exception as e:
        gg_news = google_news(coin, start_date, end_date)
        news = gg_news

    model_name = MODEL

    # Build instruction prompt
    prompt = f"""
Current Bitcoin price: ${last_price}
24h price change: {get_24h_change}%
7d price change: {get_7d_change}%
30d price change: {get_30d_change}%

Here are the latest Bitcoin news items:
{news}

INSTRUCTION:
For each news item, in order:
1. **Extraction**: Summarize the key fact or development.
2. **Impact**: Explain how that development might affect Bitcoin's price.
3. **Signal**: Give a preliminary signal for *that item* – "buy", "sell", or "hold" – with a confidence score between 0.0 and 1.0.

**BALANCE**
**Initial Investment Cash: $100000**
**Current owned Cash: ${cash}**
**Current owned BTC: {btc_quantity} BTC ~ ${btc_quantity * last_price}**
**You can only buy if you have cash and sell if you have Bitcoin. If you have no cash or Bitcoin, you should hold with 1.0 confidence.**

After analyzing all news items, evaluate the price trends:
- If prices are falling (negative % changes): This suggests a potential buying opportunity
- If prices are steadily rising (positive % changes): Consider holding to capture more of the uptrend
- If prices show extreme spikes or signs of peaking: Consider selling to lock in profits
- Consider price volatility, momentum, and trend strength when making your decision

Now make your **final decision** by combining news analysis AND price trends into a single JSON object exactly in this format (and nothing else):

```json
"choice": "<buy|sell|hold>",
"confidence": "<float>"
```

REMEMBER:
Buy when prices are low or falling
Hold during steady uptrends to maximize gains
Sell at relative peaks or signs of trend reversal
Always check your balance before finalizing decisions
"""

    # Stream the completion
    full_response = ""
    print("\nStreaming response from LM Studio:\n" + "-"*50)
    for chunk in stream_from_lm(model_name, prompt):
        delta = chunk.choices[0].delta.content
        if delta is not None:  # Check if delta is not None before concatenating
            print(delta, end="", flush=True)
            full_response += delta
    print("\n" + "-"*50 + "\n")

    # response = json.loads(full_response)
    # choice = response.get("choice")
    # confidence = response.get("confidence")
    # Extract JSON result
    matches = re.findall(
        r'"choice"\s*:\s*"(buy|sell|hold)"\s*,\s*"confidence"\s*:\s*"?([\d\.]+)"?',
        full_response, re.IGNORECASE
    )
    if matches:
        # Take the last match as it should be the final decision
        choice, confidence_str = matches[-1]
        confidence = float(confidence_str)
    else:
        choice, confidence = "hold", 1.0

    return choice, confidence

# if __name__ == "__main__":
#     start_date = datetime(2025, 5, 14)
#     end_date = datetime(2025, 5, 15)
#     cash = 1000
#     btc_quantity = 0
#     coin = "BTC"
#     last_price = 100000
#     get_24h_change = 10
#     get_7d_change = 10
#     get_30d_change = 10
#     choice, confidence = get_recommendation(coin, start_date, end_date, cash, btc_quantity, get_24h_change, get_7d_change, get_30d_change, last_price)
#     print(choice, confidence)
