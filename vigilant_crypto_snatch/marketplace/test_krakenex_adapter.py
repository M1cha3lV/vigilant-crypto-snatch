import datetime
from typing import Callable
from typing import Dict

import pytest

from .interface import BuyError
from .interface import KrakenConfig
from .interface import TickerError
from .krakenex_adaptor import KrakenexMarketplace


class KrakenexMock:
    def __init__(self, methods: Dict[str, Callable] = None):
        if methods:
            self.methods = methods
        else:
            self.methods = {}

    def query_public(self, command: str, parameters: Dict = None) -> Dict:
        return self.methods[command](parameters)

    def query_private(self, command: str, parameters: Dict = None) -> Dict:
        return self.methods[command](parameters)


def stub_ticker_success(parameters: Dict) -> Dict:
    assert parameters["pair"] in ["XBTEUR", "BTCEUR", "XXBTZEUR"]
    return {
        "error": [],
        "result": {
            "XXBTZEUR": {
                "a": ["50162.20000", "1", "1.000"],
                "b": ["50162.10000", "2", "2.000"],
                "c": ["50162.20000", "0.00196431"],
                "v": ["1194.93544125", "3142.87839034"],
                "p": ["50218.07897", "50141.26546"],
                "t": [7355, 32353],
                "l": ["49750.00000", "49517.80000"],
                "h": ["50552.70000", "50657.00000"],
                "o": "50023.50000",
            }
        },
    }


def stub_ticker_error(parameters: Dict) -> Dict:
    return {"error": ["EQuery:Unknown asset pair"]}


def stub_balance_full(parameters: Dict) -> Dict:
    return {
        "error": [],
        "result": {
            "ZEUR": "6789.1234",
            "XXBT": "1234.5678",
        },
    }


def stub_balance_empty(parameters: Dict) -> Dict:
    return {
        "error": [],
    }


def stub_balance_error(parameters: Dict) -> Dict:
    return {
        "error": ["Some error"],
    }


def stub_add_order_success(parameters: Dict) -> Dict:
    assert parameters["pair"] == "XBTEUR"
    assert parameters["ordertype"] == "market"
    assert parameters["type"] == "buy"
    assert parameters["volume"] == "100.0"
    assert parameters["oflags"] == "fciq"

    return {
        "error": [],
        "result": {
            "descr": {
                "order": "buy 2.12340000 XBTUSD @ limit 45000.1 with 2:1 leverage",
                "close": "close position @ stop loss 38000.0 -> limit 36000.0",
            },
            "txid": ["OUF4EM-FRGI2-MQMWZD"],
        },
    }


def stub_add_order_error(parameters: Dict) -> Dict:
    return {
        "error": ["EOrder:Insufficient funds"],
    }


def test_get_name() -> None:
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config)
    assert market.get_name() == "Kraken"


def test_get_spot_price_success() -> None:
    krakenex_interface = KrakenexMock({"Ticker": stub_ticker_success})
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config, krakenex_interface)
    now = datetime.datetime.now()
    price = market.get_spot_price("BTC", "EUR", now)
    assert price.timestamp == now
    assert price.coin == "BTC"
    assert price.fiat == "EUR"
    assert price.last == 50162.2


def test_get_spot_price_error() -> None:
    krakenex_interface = KrakenexMock({"Ticker": stub_ticker_error})
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config, krakenex_interface)
    now = datetime.datetime.now()
    with pytest.raises(TickerError):
        price = market.get_spot_price("AAA", "AAA", now)


def test_balance_full() -> None:
    krakenex_interface = KrakenexMock({"Balance": stub_balance_full})
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config, krakenex_interface)
    balances = market.get_balance()
    assert balances == {"EUR": 6789.1234, "BTC": 1234.5678}


def test_balance_empty() -> None:
    krakenex_interface = KrakenexMock({"Balance": stub_balance_empty})
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config, krakenex_interface)
    balances = market.get_balance()
    assert balances == {}


def test_balance_error() -> None:
    krakenex_interface = KrakenexMock({"Balance": stub_balance_error})
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config, krakenex_interface)
    with pytest.raises(TickerError):
        market.get_balance()


def test_place_order_success() -> None:
    krakenex_interface = KrakenexMock({"AddOrder": stub_add_order_success})
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config, krakenex_interface)
    market.place_order("BTC", "EUR", 100.0)


def test_place_order_error() -> None:
    krakenex_interface = KrakenexMock({"AddOrder": stub_add_order_error})
    config = KrakenConfig("mock", "mock", False, {})
    market = KrakenexMarketplace(config, krakenex_interface)
    with pytest.raises(BuyError):
        market.place_order("BTC", "EUR", 100.0)
