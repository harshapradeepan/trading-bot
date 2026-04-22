from typing import Optional
from .logging_config import setup_logger

logger = setup_logger("validators")

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> None:
    """Validate all user inputs before any API call. Raises ValueError on failure."""

    # Symbol
    if not symbol or not isinstance(symbol, str) or len(symbol.strip()) < 3:
        raise ValueError(f"Invalid symbol '{symbol}'. Example: BTCUSDT")
    logger.debug("Symbol OK: %s", symbol.upper())

    # Side
    if side.strip().upper() not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be: BUY or SELL")
    logger.debug("Side OK: %s", side.upper())

    # Order type
    if order_type.strip().upper() not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be: MARKET, LIMIT, or STOP_MARKET"
        )
    logger.debug("Order type OK: %s", order_type.upper())

    # Quantity
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be > 0. Got: {qty}")
    logger.debug("Quantity OK: %s", qty)

    ot = order_type.strip().upper()

    # Price — required for LIMIT
    if ot == "LIMIT":
        if price is None:
            raise ValueError("--price is required for LIMIT orders.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"Price '{price}' is not a valid number.")
        if p <= 0:
            raise ValueError(f"Price must be > 0. Got: {p}")
        logger.debug("Price OK: %s", p)

    # Stop price — required for STOP_MARKET
    if ot == "STOP_MARKET":
        if stop_price is None:
            raise ValueError("--stop-price is required for STOP_MARKET orders.")
        try:
            sp = float(stop_price)
        except (TypeError, ValueError):
            raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
        if sp <= 0:
            raise ValueError(f"Stop price must be > 0. Got: {sp}")
        logger.debug("Stop price OK: %s", sp)

    logger.debug("All inputs passed validation.")
