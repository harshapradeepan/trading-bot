import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import setup_logger

logger = setup_logger("client")
BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    """
    Binance Futures Testnet HTTP client with HMAC-SHA256 request signing.
    Used only when MOCK_MODE is disabled.
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        logger.debug("BinanceClient initialised — base URL: %s", BASE_URL)

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: Dict[str, Any]) -> str:
        query_string = urlencode(params)
        sig = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        logger.debug("Request signed. Params: %s", list(params.keys()))
        return sig

    def post(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        params = params or {}
        params["timestamp"] = self._timestamp()
        params["signature"] = self._sign(params)
        url = f"{BASE_URL}{endpoint}"

        safe = {k: v for k, v in params.items() if k != "signature"}
        logger.debug("POST %s | params: %s", url, safe)

        try:
            resp = self.session.post(url, params=params, timeout=10)
            return self._handle(resp)
        except requests.exceptions.ConnectionError as e:
            logger.error("Network error on POST %s: %s", endpoint, e)
            raise ConnectionError(f"Cannot reach Binance testnet: {e}") from e
        except requests.exceptions.Timeout:
            logger.error("Timeout on POST %s", endpoint)
            raise TimeoutError("Request timed out — check your connection.")

    def _handle(self, resp: requests.Response) -> Dict:
        logger.debug("Response [HTTP %s]: %s", resp.status_code, resp.text[:600])
        if resp.status_code == 200:
            return resp.json()
        try:
            err = resp.json()
            code = err.get("code", resp.status_code)
            msg = err.get("msg", "Unknown error")
        except Exception:
            code, msg = resp.status_code, resp.text
        logger.error("Binance API error %s: %s", code, msg)
        raise RuntimeError(f"Binance API Error {code}: {msg}")
