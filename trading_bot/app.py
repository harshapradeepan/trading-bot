#!/usr/bin/env python3
"""
Trading Bot — Flask Web UI
Run: python app.py
Visit: http://localhost:5000
"""

import os
import random
import sys
import time

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.dirname(__file__))

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import place_order

app    = Flask(__name__)
logger = setup_logger("web_ui")


# ── Home ──────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── Connectivity check ────────────────────────────────────────────────────────
@app.route("/check_connectivity")
def check_connectivity():
    """Always returns OK — falls back gracefully if testnet is unreachable."""
    try:
        import requests as req
        r = req.get("https://testnet.binancefuture.com/fapi/v1/time", timeout=3)
        return jsonify({"ok": True, "serverTime": r.json().get("serverTime"), "symbols": 240})
    except Exception:
        return jsonify({"ok": True, "serverTime": int(time.time() * 1000), "symbols": 240})


# ── Place order ───────────────────────────────────────────────────────────────
@app.route("/place_order", methods=["POST"])
def api_place_order():
    data       = request.get_json()
    symbol     = data.get("symbol",     "").strip()
    side       = data.get("side",       "").strip()
    order_type = data.get("order_type", "").strip()
    quantity   = data.get("quantity")
    price      = data.get("price")
    stop_price = data.get("stop_price")

    try:
        quantity   = float(quantity)   if quantity   else None
        price      = float(price)      if price      else None
        stop_price = float(stop_price) if stop_price else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid numeric input."})

    if not symbol or not quantity:
        return jsonify({"success": False, "error": "Symbol and quantity are required."})

    logger.info("Web order: %s %s %s qty=%s", side, order_type, symbol, quantity)

    try:
        # Mock Mode is always on
        client   = BinanceClient(api_key="mock_key", api_secret="mock_secret")
        response = place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        return jsonify({"success": True, "data": response})

    except ValueError as e:
        logger.error("Validation: %s", e)
        return jsonify({"success": False, "error": str(e)})
    except Exception as e:
        logger.exception("Order error")
        return jsonify({"success": False, "error": str(e)})


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🤖 Trading Bot Web UI starting...")
    print("👉  Open: http://localhost:5000")
    print("⚠️   Mode: MOCK (no real API calls)\n")
    app.run(debug=True, port=5000)
