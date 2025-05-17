from get_news import google_news, alpaca_news
import re
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY")
LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL")
MODEL = os.getenv("LM_MODEL_NAME")

client = OpenAI(api_key=LMSTUDIO_API_KEY, base_url=LMSTUDIO_API_URL)


def stream_from_lm(model_name: str, prompt: str, temperature=0.7, top_p=0.9):
    """
    Stream chat completions using only user/assistant roles.
    """
    user_prompt = (
        "You are a helpful financial assistant.\n\n"
        + prompt
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        top_p=top_p,
        stream=True
    )
    return response


def get_recommendation(coin: str, start_date: str, end_date: str):
    gg_news = google_news(coin, start_date, end_date)
    # alp_news = alpaca_news(coin, start_date, end_date)
    news = gg_news

    model_name = MODEL

    # Build instruction prompt
    prompt = f"""Here are the latest Bitcoin news items:
{news}

INSTRUCTION:
For each news item, in order:
1. **Extraction**: Summarize the key fact or development.
2. **Impact**: Explain how that development might affect Bitcoin's price.
3. **Signal**: Give a preliminary signal for *that item* – "buy", "hold", or "sell" – with a confidence score between 0.0 and 1.0.

After you've done that for every item, write a **final decision** by combining all the signals into a single JSON object exactly in this format (and nothing else):

"choice": "<buy|sell|hold>",
"confidence": "<float>"
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

    response = json.loads(full_response)
    choice = response.get("choice")
    confidence = response.get("confidence")
    # Extract JSON result
    m = re.search(
        r'"choice"\s*:\s*"(buy|sell|hold)"\s*,\s*"confidence"\s*:\s*"?([\d\.]+)"?',
        full_response, re.IGNORECASE
    )
    if m:
        choice, confidence = m.group(1), float(m.group(2))
    else:
        choice, confidence = "hold", 1.0

    return choice, confidence
