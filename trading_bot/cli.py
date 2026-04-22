#!/usr/bin/env python3
"""
Trading Bot — CLI
Usage: python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
"""

import argparse
import os
import sys

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import format_response, place_order

logger = setup_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="🤖 Binance Futures Testnet Trading Bot (Mock Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET      --quantity 0.01
  python cli.py --symbol BTCUSDT --side BUY  --type LIMIT        --quantity 0.01 --price 50000
  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET  --quantity 0.01 --stop-price 30000
        """,
    )

    parser.add_argument("--symbol",   required=True,  help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",     required=True,  choices=["BUY", "SELL"])
    parser.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        help="Order type"
    )
    parser.add_argument("--quantity", required=True,  type=float, help="Order quantity")
    parser.add_argument("--price",                    type=float, default=None, help="Limit price (LIMIT orders)")
    parser.add_argument("--stop-price", dest="stop_price", type=float, default=None, help="Stop price (STOP_MARKET orders)")
    parser.add_argument("--api-key",    default=None, help="Binance API key (not needed in Mock Mode)")
    parser.add_argument("--api-secret", default=None, help="Binance API secret (not needed in Mock Mode)")

    return parser


def resolve_credentials(args) -> tuple:
    """Return mock credentials in Mock Mode; otherwise read from args or env."""
    if os.getenv("MOCK_MODE", "true").lower() == "true":
        return "mock_key", "mock_secret"

    api_key    = args.api_key    or os.environ.get("BINANCE_API_KEY",    "").strip()
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print("\n❌ ERROR: API credentials not found.")
        print("   Set BINANCE_API_KEY and BINANCE_API_SECRET, or use --api-key / --api-secret\n")
        sys.exit(1)

    return api_key, api_secret


def early_validate(args) -> None:
    """Catch missing required args before the API call."""
    if args.order_type.upper() == "LIMIT" and args.price is None:
        print("\n❌ ERROR: --price is required for LIMIT orders\n")
        sys.exit(1)
    if args.order_type.upper() == "STOP_MARKET" and args.stop_price is None:
        print("\n❌ ERROR: --stop-price is required for STOP_MARKET orders\n")
        sys.exit(1)


def print_summary(args) -> None:
    mock_tag = "  ⚠️  MOCK MODE — no real API calls\n" if os.getenv("MOCK_MODE", "true").lower() == "true" else ""
    print("\n" + "=" * 54)
    print("         📋  ORDER REQUEST SUMMARY")
    print("=" * 54)
    if mock_tag:
        print(mock_tag.rstrip())
    print(f"  Symbol      : {args.symbol.upper()}")
    print(f"  Side        : {args.side.upper()}")
    print(f"  Type        : {args.order_type.upper()}")
    print(f"  Quantity    : {args.quantity}")
    if args.order_type.upper() == "LIMIT":
        print(f"  Price       : {args.price}")
    if args.order_type.upper() == "STOP_MARKET":
        print(f"  Stop Price  : {args.stop_price}")
    print("=" * 54)


def main():
    parser = build_parser()
    args   = parser.parse_args()

    early_validate(args)
    api_key, api_secret = resolve_credentials(args)

    logger.debug(
        "CLI: symbol=%s side=%s type=%s qty=%s",
        args.symbol, args.side, args.order_type, args.quantity,
    )

    print_summary(args)

    try:
        client = BinanceClient(api_key=api_key, api_secret=api_secret)
        print("\n⏳ Processing order...\n")

        response = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )

        print(format_response(response, args.order_type))

    except ValueError as e:
        logger.error("Validation error: %s", e)
        print(f"\n❌ Validation Error: {e}\n")
        sys.exit(1)
    except (ConnectionError, TimeoutError) as e:
        logger.error("Network error: %s", e)
        print(f"\n❌ Network Error: {e}\n")
        sys.exit(1)
    except RuntimeError as e:
        logger.error("API error: %s", e)
        print(f"\n❌ API Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n❌ Unexpected Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
