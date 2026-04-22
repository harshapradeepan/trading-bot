# 🤖 Binance Futures Trading Bot — Mock Mode

A Python trading bot for Binance Futures Testnet (USDT-M) with a Flask Web UI and CLI interface.

> Note: The Binance Futures Testnet API is geo-restricted in several regions and has connectivity issues. This project is fully implemented to spec with a Mock Mode that simulates all orders locally — no API credentials required. The real API client (`bot/client.py`) is implemented with full HMAC-SHA256 signing and is ready to use when the testnet becomes accessible.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py           # Binance HTTP client + HMAC-SHA256 signing
│   ├── orders.py           # Order placement logic + mock fallback + response formatting
│   ├── validators.py       # Input validation (symbol, side, type, qty, price)
│   └── logging_config.py   # File + console logger (daily rotation)
├── templates/
│   └── index.html          # Web UI — dark theme, order form, activity log
├── app.py                  # Flask web server
├── cli.py                  # CLI entry point (argparse)
├── logs/                   # Auto-created — daily log files
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

## How to Run

### Web UI

```bash
python app.py
```

Open http://localhost:5000 in your browser.

### CLI

```bash
# MARKET BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# MARKET SELL
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1

# LIMIT BUY
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 50000

# LIMIT SELL
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 90000

# STOP_MARKET BUY  (bonus order type)
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 30000
```

No environment variables are needed — Mock Mode is on by default.

---

## Example CLI Output

```
======================================================
         📋  ORDER REQUEST SUMMARY
======================================================
  ⚠️  MOCK MODE — no real API calls
  Symbol      : BTCUSDT
  Side        : BUY
  Type        : MARKET
  Quantity    : 0.01
======================================================

⏳ Processing order...

======================================================
         ✅  ORDER PLACED SUCCESSFULLY
======================================================
  [SIMULATED — Mock Mode]
  Order ID      : 843209590
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Orig Qty      : 0.01
  Executed Qty  : 0.01
  Avg Price     : 83762.18
  Status        : FILLED
  Time in Force : GTC
======================================================
```

---

## Order Types Supported

| Type | Requires | Status on Fill |
|---|---|---|
| MARKET | symbol, side, quantity | FILLED immediately |
| LIMIT | + price | NEW (waits for price) |
| STOP_MARKET | + stop-price | NEW (triggers at stop) |

---

## Validation & Error Handling

| Scenario | Behaviour |
|---|---|
| Missing `--price` for LIMIT | Error shown before processing |
| Missing `--stop-price` for STOP_MARKET | Error shown before processing |
| Invalid side (not BUY/SELL) | ValidationError, logged |
| Invalid symbol (< 3 chars) | ValidationError, logged |
| Quantity ≤ 0 | ValidationError, logged |
| Network failure / timeout | Friendly message, logged |
| Binance API error | Error code + message shown |

---

## Logging

Logs are saved to `logs/trading_bot_YYYYMMDD.log`:

| Level | Content |
|---|---|
| DEBUG | Validator steps, request params, client init |
| INFO | Order ID, symbol, status on each order |
| WARNING | Mock mode active notification |
| ERROR | Validation failures, API/network errors |

Console only shows WARNING and above — keeping CLI output clean.

---

## Assumptions

- All orders target USDT-M Futures Testnet
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled)
- STOP_MARKET triggers at `stopPrice` then fills at market
- Mock MARKET orders are immediately FILLED; LIMIT and STOP_MARKET are NEW
- Mock prices use reference values with a small random spread to simulate market movement
- The bot places orders only — no position management or order cancellation
- Quantity precision should follow Binance symbol rules (e.g. min 0.001 BTC)
