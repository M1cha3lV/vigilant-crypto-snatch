import datetime
import typing

import krakenex
import vigilant_crypto_snatch.datamodel

from vigilant_crypto_snatch import marketplace

from vigilant_crypto_snatch import logger


class KrakenexMarketplace(marketplace.Marketplace):
    def __init__(self, api_key: str, api_secret: str):
        # self.api_key = api_key
        # self.api_secret = api_secret
        self.handle = krakenex.API(api_key, api_secret)

    def get_name(self) -> str:
        return "Kraken"

    def get_spot_price(
        self, coin: str, fiat: str, now: datetime.datetime
    ) -> vigilant_crypto_snatch.datamodel.Price:
        answer = self.handle.query_public("Ticker", {"pair": f"{coin}{fiat}"})
        raise_error(answer, marketplace.TickerError)
        close = float(list(answer["result"].values())[0]["c"][0])
        logger.debug(f"Retrieved {close} for {fiat}/{coin} from Krakenex.")
        price = vigilant_crypto_snatch.datamodel.Price(
            timestamp=now, last=close, coin=coin, fiat=fiat
        )
        return price

    def get_balance(self) -> dict:
        answer = self.handle.query_private("Balance")
        raise_error(answer, marketplace.TickerError)
        return {currency: float(value) for currency, value in answer["result"].items()}

    def place_order(self, coin: str, fiat: str, volume: float) -> None:
        answer = self.handle.query_private(
            "AddOrder",
            {
                "pair": f"{coin}{fiat}",
                "ordertype": "market",
                "type": f"buy",
                "volume": str(volume),
                # 'validate': 'validate',
            },
        )
        raise_error(answer, marketplace.BuyError)


def raise_error(answer: dict, exception: typing.Type[Exception]):
    if len(answer["error"]) > 0:
        raise exception(answer["error"])
