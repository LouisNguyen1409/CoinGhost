from get_news import google_news, alpaca_news
import mlx.core as mx
from mlx_lm import load, generate
import torch
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread
import re
from dotenv import load_dotenv
from openai import OpenAI
import os

model_name = "mlx-community/gemma-3-27b-it-4bit"


def get_recommendation(coin: str, start_date: str, end_date: str):
    # gg_news = google_news(coin, start_date, end_date)
    alp_news = alpaca_news(coin, start_date, end_date)
    news = alp_news

    # UNCOMMENT THIS TO USE GEMMA MODEL
    # model_name = "mlx-community/gemma-3-27b-it-4bit"
    # model, tokenizer = load(model_name)
    # prompt = f"""You are a helpful financial assistant.
    # Here are the latest Bitcoin news items:
    # {news}

    # INSTRUCTION:
    # For each news item, in order:
    # 1. **Extraction**: Summarize the key fact or development.
    # 2. **Impact**: Explain how that development might affect Bitcoin's price.
    # 3. **Signal**: Give a preliminary signal for *that item* – "buy", "hold", or "sell" – with a confidence score between 0.0 and 1.0.

    # After you've done that for every item, write a **final decision** by combining all the signals into a single JSON object exactly in this format (and nothing else):

    # "choice": "<buy|sell|hold>",
    # "confidence": "<float>"
    # """
    # response = generate(
    #     model,
    #     tokenizer,
    #     prompt=prompt,
    #     max_tokens=100000,
    #     temperature=0.7
    # )

    # print(response)

    # UNCOMMENT THIS TO USE MISTRAL MODEL
    # model_name = "mistralai/Mistral-7B-Instruct-v0.3"
    # tokenizer = AutoTokenizer.from_pretrained(model_name)
    # tokenizer.pad_token = tokenizer.eos_token
    # tokenizer.padding_side = "left"
    # device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    # model = AutoModelForCausalLM.from_pretrained(
    #     model_name,
    #     torch_dtype=torch.float16,      # Use half precision
    #     low_cpu_mem_usage=True,        # Optimize CPU memory usage
    #     device_map={"": device}        # Map to MPS device
    # )
    # print(len(news[:7]))
    # prompt = f"""<s>[INST]
    # SYSTEM: You are a helpful financial assistant.

    # USER: Here are the latest Bitcoin news items:
    # {news[:6]}

    # INSTRUCTION:
    # For each news item, in order:
    # 1. **Extraction**: Summarize the key fact or development.
    # 2. **Impact**: Explain how that development might affect Bitcoin's price.
    # 3. **Signal**: Give a preliminary signal for *that item* – "buy", "hold", or "sell" – with a confidence score between 0.0 and 1.0.

    # After you've done that for every item, write a **final decision** by combining all the signals into a single JSON object exactly in this format (and nothing else):

    # "choice": "<buy|sell|hold>",
    # "confidence": "<float>"
    # [/INST]"""

    # inputs = tokenizer(
    #     prompt,
    #     return_tensors="pt",
    #     padding=True,
    #     add_special_tokens=True
    # )
    # inputs = {k: v.to(device) for k, v in inputs.items()}

    # # Set up the streamer for asynchronous output
    # streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    # # Generate with optimized settings for MPS
    # generation_kwargs = {
    #     "input_ids": inputs["input_ids"],
    #     "attention_mask": inputs["attention_mask"],
    #     "max_new_tokens": 100000,
    #     "temperature": 0.7,
    #     "top_p": 0.9,
    #     "do_sample": True,
    #     "pad_token_id": tokenizer.pad_token_id,
    #     "eos_token_id": tokenizer.eos_token_id,
    #     "streamer": streamer
    # }

    # # Start generation in a separate thread
    # thread = Thread(target=model.generate, kwargs=generation_kwargs)
    # thread.start()

    # # Process the streamed output in the main thread
    # full_response = ""
    # print("\nStreaming response:\n" + "-"*50)
    # for text in streamer:
    #     print(text, end="", flush=True)
    #     full_response += text
    # print("\n" + "-"*50 + "\n")

    # # Wait for the generation to complete
    # thread.join()

    # # Extract only the JSON part from the response
    # m = re.search(
    #     r'[\s\S]*["\'](choice)["\']\s*:\s*["\'](buy|sell|hold)["\'],\s*["\'](confidence)["\']\s*:\s*(["\']{0,1})([\d\.]+)(["\']{0,1})', full_response, re.IGNORECASE)
    # if m:
    #     choice = m.group(2)
    #     confidence = float(m.group(5))
    # else:
    #     # Default values if JSON can't be extracted
    #     choice = "hold"
    #     confidence = 1

    # UNCOMMENT THIS TO USE OPENAI MODEL
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
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

    # Stream the response
    stream = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    # Print chunks as they arrive
    full_response = ""
    print("\nStreaming response:\n" + "-"*50)
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    print("\n" + "-"*50)

    # Extract the JSON part from the response
    m = re.search(
        r'[\s\S]*["\'](choice)["\']\s*:\s*["\'](buy|sell|hold)["\'],\s*["\'](confidence)["\']\s*:\s*(["\']{0,1})([\d\.]+)(["\']{0,1})', full_response, re.IGNORECASE)
    if m:
        choice = m.group(2)
        confidence = float(m.group(5))
    else:
        # Default values if JSON can't be extracted
        choice = "hold"
        confidence = 1

    return choice, confidence
