import datetime
import logging
import os
import json
import typing

import requests
import pandas as pd
import matplotlib.pyplot as pl
import tqdm
import numpy as np

logger = logging.getLogger("vigilant_crypto_snatch")
report_dir = os.path.expanduser("~/.local/vigilant-crypto-snatch/report/")


def make_report(coin: str, fiat: str, api_key: str):
    data = get_hourly_data(coin, fiat, api_key)
    plot_close(data)
    plot_drop_survey(data)


def get_hourly_data(coin: str, fiat: str, api_key: str) -> pd.DataFrame:
    cache_file = f"~/.cache/vigilant-crypto-snatch/hourly_{coin}_{fiat}.js"
    cache_file = os.path.expanduser(cache_file)
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    if os.path.exists(cache_file):
        logger.debug("Cached historic data exists.")
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
        if mtime > datetime.datetime.now() - datetime.timedelta(days=1):
            logger.debug("Cached historic data is recent. Loading that.")
            with open(cache_file) as f:
                return pd.DataFrame(json.load(f))

    logger.debug("Requesting historic data from Crypto Compare.")
    timestamp = int(datetime.datetime.now().timestamp())
    url = (
        f"https://min-api.cryptocompare.com/data/histohour"
        f"?api_key={api_key}"
        f"&fsym={coin}&tsym={fiat}"
        f"&limit=2000&toTs={timestamp}"
    )
    r = requests.get(url)
    data = r.json()["Data"]
    with open(cache_file, "w") as f:
        json.dump(data, f)
    return pd.DataFrame(data)


def plot_close(data: pd.DataFrame) -> None:
    fig, ax = pl.subplots()
    ax.plot(data["time"], data["close"])
    ax.set_title('Close Price')
    ax.set_xlabel('Time')
    ax.set_ylabel('Close')
    save_figure(fig, 'close')

def save_figure(fig: pl.Figure, name: str) -> None:
    os.makedirs(report_dir, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(report_dir, f"{name}.pdf"))
    fig.savefig(os.path.join(report_dir, f"{name}.png"), dpi=300)
    fig.savefig(os.path.join(report_dir, f"{name}.svg"))


def plot_drop_hist(data: pd.DataFrame) -> None:
    pl.clf()
    pl.hist(data["close"].shift() / data["close"], bins="sturges")
    pl.show()

    pl.clf()
    pl.hist(data["close"].shift(2) / data["close"], bins="sturges")
    pl.show()

    pl.clf()
    pl.hist(data["close"].shift(3) / data["close"], bins="sturges")
    pl.show()

    pl.clf()
    pl.hist(data["close"].shift(24) / data["close"], bins="sturges")
    pl.show()

    pl.clf()
    pl.hist(data["close"].shift(7 * 24) / data["close"], bins="sturges")
    pl.show()


def plot_drop_survey(data):
    hours, drops, factor = drop_survey(data)
    fig, ax = pl.subplots()
    img = ax.pcolormesh(hours, drops * 100, factor, cmap="turbo", shading='nearest')
    pl.colorbar(img, ax=ax)
    ax.set_title("BTC / EUR")
    ax.set_xlabel("Delay / h")
    ax.set_ylabel("Drop / %")
    save_figure(fig, "survey")

def drop_survey(data: pd.DataFrame) -> typing.Tuple[np.array, np.array, np.array]:
    hours = np.arange(1, 24)
    drops = np.linspace(0.01, 0.30, 5)
    factor = np.zeros(hours.shape + drops.shape)
    for i, hour in tqdm.tqdm(enumerate(hours)):
        for j, drop in enumerate(drops):
            factor[i, j] = compute_gains(data, hour, drop)[2]
    return hours, drops, factor.T


def compute_gains(
    df: pd.DataFrame, hours: int, drop: float
) -> typing.Tuple[float, float, float]:
    close_shift = df["close"].shift(hours)
    ratio = df["close"] / close_shift
    btc = 0.0
    eur = 0.0
    last = -hours
    for i in range(len(df)):
        if ratio[i] < (1 - drop) and last + hours <= i:
            last = i
            btc += 1.0 / df["close"][i]
            eur += 1.0
    return btc, eur, btc / eur if eur > 0 else 0.0


def compute_dca(df: pd.DataFrame, hours: int) -> typing.Tuple[float, float, float]:
    btc = 0.0
    eur = 0.0
    last = -hours
    for i in range(len(df)):
        if last + hours <= i:
            last = i
            btc += 1.0 / df["close"][i]
            eur += 1.0
    return btc, eur, btc / eur if eur > 0 else 0.0
