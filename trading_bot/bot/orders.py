import os
import random
import time
from typing import Dict, Optional

from .client import BinanceClient
from .logging_config import setup_logger
from .validators import validate_inputs

logger = setup_logger("orders")
ORDER_ENDPOINT = "/fapi/v1/order"

# Mock reference prices per symbol
MOCK_PRICES = {
    "BTCUSDT":  84000.0,
    "ETHUSDT":  3200.0,
    "BNBUSDT":  580.0,
    "SOLUSDT":  145.0,
    "XRPUSDT":  0.52,
    "DOGEUSDT": 0.12,
}


def _mock_fill_price(symbol: str, price: Optional[float], stop_price: Optional[float]) -> float:
    if price:
        return float(price)
    if stop_price:
        return float(stop_price)
    base = MOCK_PRICES.get(symbol.upper(), 1000.0)
    # Add a small random spread to simulate market movement
    return round(base * (1 + (random.random() - 0.5) * 0.006), 2)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Dict:
    """
    Place a MARKET, LIMIT, or STOP_MARKET order.
    Runs in Mock Mode when MOCK_MODE=true (default).
    """

    symbol     = symbol.strip().upper()
    side       = side.strip().upper()
    order_type = order_type.strip().upper()

    validate_inputs(symbol, side, order_type, quantity, price, stop_price)

    # ── MOCK MODE ──────────────────────────────────────────────────────────────
    if os.getenv("MOCK_MODE", "true").lower() == "true":
        logger.warning("MOCK MODE ACTIVE — no real API call made")

        fill_price  = _mock_fill_price(symbol, price, stop_price)
        is_filled   = order_type == "MARKET"
        order_id    = random.randint(100_000_000, 999_999_999)

        mock_response = {
            "orderId":      order_id,
            "symbol":       symbol,
            "side":         side,
            "type":         order_type,
            "origQty":      str(quantity),
            "executedQty":  str(quantity) if is_filled else "0",
            "price":        str(price)      if price      else "0",
            "avgPrice":     str(fill_price) if is_filled  else "0",
            "status":       "FILLED" if is_filled else "NEW",
            "timeInForce":  "GTC",
            "stopPrice":    str(stop_price) if stop_price else "",
            "time":         int(time.time() * 1000),
        }

        logger.info(
            "Mock order | orderId=%s symbol=%s side=%s type=%s qty=%s status=%s",
            order_id, symbol, side, order_type, quantity, mock_response["status"],
        )
        return mock_response

    # ── REAL API FLOW ──────────────────────────────────────────────────────────
    params: Dict = {
        "symbol":   symbol,
        "side":     side,
        "type":     order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        params["price"]       = price
        params["timeInForce"] = "GTC"

    if order_type == "STOP_MARKET":
        params["stopPrice"] = stop_price

    logger.info(
        "Placing order | type=%s side=%s symbol=%s qty=%s%s%s",
        order_type, side, symbol, quantity,
        f" price={price}"          if price      else "",
        f" stopPrice={stop_price}" if stop_price else "",
    )

    response = client.post(ORDER_ENDPOINT, params=params)

    logger.info(
        "Order success | orderId=%s status=%s executedQty=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
    )
    return response


def format_response(response: Dict, order_type: str) -> str:
    """Format the API / mock response into a clean human-readable summary."""

    avg_price = response.get("avgPrice") or response.get("price") or "N/A"
    stop      = response.get("stopPrice", "")
    mode_tag  = "  [SIMULATED — Mock Mode]\n" if os.getenv("MOCK_MODE", "true").lower() == "true" else ""

    lines = [
        "",
        "=" * 54,
        "         ✅  ORDER PLACED SUCCESSFULLY",
        "=" * 54,
        mode_tag.rstrip(),
        f"  Order ID      : {response.get('orderId', 'N/A')}",
        f"  Symbol        : {response.get('symbol',  'N/A')}",
        f"  Side          : {response.get('side',    'N/A')}",
        f"  Type          : {response.get('type',    'N/A')}",
        f"  Orig Qty      : {response.get('origQty', 'N/A')}",
        f"  Executed Qty  : {response.get('executedQty', 'N/A')}",
        f"  Avg Price     : {avg_price}",
    ]

    if stop:
        lines.append(f"  Stop Price    : {stop}")

    lines += [
        f"  Status        : {response.get('status',      'N/A')}",
        f"  Time in Force : {response.get('timeInForce', 'N/A')}",
        "=" * 54,
        "",
    ]

    return "\n".join(lines)
