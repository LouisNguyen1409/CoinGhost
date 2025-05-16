# CoinGhost v1

CoinGhost is an cryptocurrency trading bot that uses natural language models to analyze news data and make trading decisions for cryptocurrencies.

## Features

- Automated cryptocurrency trading strategy based on news sentiment analysis
- Utilizes GPT-4.1 (with alternative options for Gemma and Mistral models)
- Fetches and analyzes latest news from Alpaca and Google News APIs
- Provides buy/sell/hold recommendations with confidence scores
- Backtesting capabilities using CCXT

## Requirements

- Python 3.11+
- MLX (Apple Silicon optimized ML library)
- OpenAI API key
- Alpaca API credentials

## Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/CoinGhost.git
cd CoinGhost
```

2. Create a virtual environment

```bash
cd v1
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
API_KEY=your_alpaca_api_key
API_SECRET=your_alpaca_api_secret
BASE_URL=https://paper-api.alpaca.markets/v2  # or your preferred Alpaca endpoint
```

## Usage

### Running the Trading Bot

```python
python v1/trading.py
```

### Testing News Analysis

You can test the news analysis component independently:

```python
python v1/get_news.py
```

## Project Structure

- `trading.py`: Contains the main MLTrader strategy class that implements the trading logic
- `llm.py`: Interface to language models (GPT-4.1, Gemma, Mistral) for news analysis
- `get_news.py`: Functions for fetching and processing news from various sources

## Configuration

You can adjust various parameters in the trading strategy:

- `cash_at_risk`: Percentage of cash to risk per trade (default: 0.2)
- `coin`: Target cryptocurrency (default: "BTC")
- Confidence threshold for trading (current: 0.7)

## License

[MIT License](LICENSE)

## Acknowledgments

- Built with [Lumibot](https://github.com/Lumiwealth/lumibot) trading framework
- Uses [Alpaca Markets](https://alpaca.markets/) API for news data
- Leverages [MLX](https://github.com/ml-explore/mlx) for optimized machine learning on Apple Silicon
