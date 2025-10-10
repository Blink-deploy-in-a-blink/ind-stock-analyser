# 🚀 F&O Market Analyzer – Intelligent Options Trading System

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![NSE](https://img.shields.io/badge/Market-NSE%20India-orange.svg)](https://nseindia.com)

Professional-grade F&O (Futures & Options) trading analysis for the Indian stock market. Real-time NSE data, strategy recommendations, confidence scoring, and actionable trade signals.

---

## ✨ Features

- 🎯 Real-time NSE option chain data (premiums, open interest, volume)
- 🧠 Multiple strategies: Bull Call Spread, Bear Put Spread, Long Call, Long Put, Long Straddle, Iron Condor
- 📊 Confidence scoring system (50% data, 25% backtest, 25% risk/reward)
- ⚡ Analyze all 189 F&O stocks in parallel
- 📈 Historical backtesting for strategy reliability
- 💡 Color-coded confidence: 🟢 High, 🟡 Medium, 🔴 Low
- 💰 Precise buy/sell details, strike prices, and premiums

---

## 🚀 Quick Start

### 1. Clone the repository
[https://github.com/Blink-deploy-in-a-blink/ind-stock-analyser.git]

cd fno-market-analyzer


### 2. Install dependencies

**On Windows:**
install.bat


**On Linux/Mac:**
chmod +x install.sh
./install.sh


---

## 🔄 Usage

**Analyze a single stock:**
python market_analyzer_v5_integrated.py RELIANCE


**Analyze all F&O stocks:**
python market_analyzer_v5_integrated.py


---

## 📋 Sample Output

🎯 RELIANCE | Current Price: ₹1,384.80 | Confidence: 75%
APPROVED Strategy: Bull Call Spread (Moderately Bullish)
EXACT TRADES:
BUY: 5 lots of 1400 CE @ ₹20.4
SELL: 5 lots of 1500 CE @ ₹1.4
NET DEBIT: ₹23,688
Max Profit: ₹101,312 | Max Loss: ₹23,688
Risk:Reward: 1:4.28


---

## 📊 Supported Strategies

| Strategy          | Market View         | Risk   | Use Case                            |
|-------------------|--------------------|--------|-------------------------------------|
| Bull Call Spread  | Moderately Bullish | Medium | Limited upside, capped risk         |
| Bear Put Spread   | Moderately Bearish | Medium | Limited downside, capped risk       |
| Long Call         | Strongly Bullish   | High   | Unlimited upside potential          |
| Long Put          | Strongly Bearish   | High   | High downside potential             |
| Long Straddle     | High Volatility    | High   | Profits from big moves              |
| Iron Condor       | Low Volatility     | Medium | Sideways market, limited risk       |

---

## ⚙️ Configuration

Edit stocks/indices in `fno_symbols.py`:

FNO_STOCKS = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']
# Add new stock symbols here
FNO_INDICES = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
# Add new index symbols here


For advanced settings, see `config.py`.

---

## 📁 Essential Files

- `market_analyzer_v5_integrated.py` - Main script
- `fno_symbols.py` - Stocks and indices
- `lot_sizes.py` - Lot size mapping
- `nse_data_fetcher_clean.py` - NSE API interface
- `config.py` - Configuration
- `install.bat`, `install.sh` - Installers
- `README.md` - This file

---

## 🙅 Files to Exclude from Git

List these in `.gitignore`:
pycache/
*.txt
config_template.py
intelligent_backtester.py
market_analyzer.py
nse_sebi_fetcher.py


---

## ⚠️ Disclaimer

- Educational and research use only.
- Not financial or investment advice.
- Options trading has high risk—verify signals and never risk more than you can afford to lose.

---

## 🤝 Contributing

1. Fork the repo, create a feature branch.
2. Add your changes and tests.
3. Open a pull request.
4. Contributions welcome!

---

## 📄 License

MIT License. See LICENSE file.

---

**Happy Trading! 🚀📈**
