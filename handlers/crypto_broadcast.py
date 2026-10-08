import os
import asyncio
import json
from datetime import datetime, timezone

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from telegram.ext import ContextTypes


# =====================================
# CONFIGURATION
# =====================================

CRYPTO_CHANNEL = os.getenv("CRYPTO_CHANNEL", "")

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
)

ALTERNATIVE_GLOBAL_URL = (
    "https://api.alternative.me/v2/global/"
)

ALTERNATIVE_FNG_URL = (
    "https://api.alternative.me/fng/?limit=1"
)


# =====================================
# COINS
# =====================================

CRYPTO_COINS = [
    {
        "id": "bitcoin",
        "symbol": "₿",
        "name": "Bitcoin",
        "ticker": "BTC",
    },
    {
        "id": "ethereum",
        "symbol": "♦️",
        "name": "Ethereum",
        "ticker": "ETH",
    },
    {
        "id": "solana",
        "symbol": "🟣",
        "name": "Solana",
        "ticker": "SOL",
    },
    {
        "id": "binancecoin",
        "symbol": "🟡",
        "name": "BNB",
        "ticker": "BNB",
    },
]


COIN_IDS = ",".join(
    coin["id"]
    for coin in CRYPTO_COINS
)


# =====================================
# HTTP HELPER
# =====================================

def _get_json_sync(url: str):
    """
    Fetch JSON from an HTTP endpoint.

    Returns:
        dict/list on success
        None on failure
    """

    request = Request(
        url,
        headers={
            "User-Agent": "NebuMine-Pro-Bot/2.0",
            "Accept": "application/json",
        },
    )

    try:

        with urlopen(
            request,
            timeout=15,
        ) as response:

            raw_data = response.read().decode(
                "utf-8"
            )

            return json.loads(raw_data)

    except (
        HTTPError,
        URLError,
        TimeoutError,
        ValueError,
        TypeError,
    ) as exc:

        print(
            "❌ Crypto API error: "
            f"{exc}"
        )

        return None

    except Exception as exc:

        print(
            "❌ Unexpected API error: "
            f"{exc}"
        )

        return None


# =====================================
# COINGECKO MARKET DATA
# =====================================

def _fetch_coin_market_data_sync():

    url = (
        f"{COINGECKO_URL}"
        f"?vs_currency=usd"
        f"&ids={COIN_IDS}"
        f"&order=market_cap_desc"
        f"&per_page=10"
        f"&page=1"
        f"&sparkline=false"
        f"&price_change_percentage=24h"
    )

    return _get_json_sync(url)


async def get_coin_market_data():

    return await asyncio.to_thread(
        _fetch_coin_market_data_sync
    )


# =====================================
# ALTERNATIVE.ME GLOBAL DATA
# =====================================

def _fetch_global_market_data_sync():

    return _get_json_sync(
        ALTERNATIVE_GLOBAL_URL
    )


async def get_global_market_data():

    return await asyncio.to_thread(
        _fetch_global_market_data_sync
    )


# =====================================
# FEAR & GREED
# =====================================

def _fetch_fear_greed_sync():

    return _get_json_sync(
        ALTERNATIVE_FNG_URL
    )


async def get_fear_greed():

    return await asyncio.to_thread(
        _fetch_fear_greed_sync
    )


# =====================================
# NUMBER FORMATTING
# =====================================

def format_price(price):

    if price is None:
        return "N/A"

    try:
        price = float(price)

    except (
        TypeError,
        ValueError,
    ):
        return "N/A"

    if price >= 1000:

        return f"${price:,.2f}"

    if price >= 1:

        return f"${price:,.2f}"

    if price >= 0.01:

        return f"${price:,.4f}"

    return f"${price:,.6f}"


def format_large_number(value):

    if value is None:
        return "N/A"

    try:
        value = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "N/A"

    if value >= 1_000_000_000_000:

        return (
            f"${value / 1_000_000_000_000:.2f}T"
        )

    if value >= 1_000_000_000:

        return (
            f"${value / 1_000_000_000:.2f}B"
        )

    if value >= 1_000_000:

        return (
            f"${value / 1_000_000:.2f}M"
        )

    if value >= 1_000:

        return (
            f"${value / 1_000:.2f}K"
        )

    return f"${value:,.2f}"


def format_percentage(change):

    if change is None:
        return "⚪ N/A"

    try:
        change = float(change)

    except (
        TypeError,
        ValueError,
    ):
        return "⚪ N/A"

    if change > 0:

        return f"📈 +{change:.2f}%"

    if change < 0:

        return f"📉 {change:.2f}%"

    return "➡️ 0.00%"


# =====================================
# FEAR & GREED FORMAT
# =====================================

def format_fear_greed(fng_data):

    try:

        data = fng_data.get(
            "data",
            [],
        )

        if not data:
            return None, None

        current = data[0]

        value = int(
            current.get(
                "value",
                0,
            )
        )

        classification = current.get(
            "value_classification",
            "Unknown",
        )

        return value, classification

    except (
        TypeError,
        ValueError,
        AttributeError,
    ):

        return None, None


# =====================================
# MARKET SIGNAL
# =====================================

def calculate_market_signal(
    coin_data,
    fear_greed_value,
):

    changes = []

    for coin in coin_data:

        change = coin.get(
            "price_change_percentage_24h"
        )

        if change is not None:

            try:
                changes.append(
                    float(change)
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

    average_change = None

    if changes:

        average_change = (
            sum(changes)
            / len(changes)
        )

    # ---------------------------------
    # Combined simple market signal
    # ---------------------------------

    score = 0

    # Price momentum
    if average_change is not None:

        if average_change >= 2:
            score += 2

        elif average_change > 0:
            score += 1

        elif average_change <= -2:
            score -= 2

        else:
            score -= 1

    # Fear & Greed
    if fear_greed_value is not None:

        if fear_greed_value >= 60:
            score += 2

        elif fear_greed_value >= 50:
            score += 1

        elif fear_greed_value <= 25:
            score -= 2

        elif fear_greed_value < 50:
            score -= 1

    if score >= 2:

        return (
            "🐂 BULLISH",
            average_change,
        )

    if score <= -2:

        return (
            "🐻 BEARISH",
            average_change,
        )

    return (
        "⚖️ NEUTRAL",
        average_change,
    )


# =====================================
# BUILD MARKET MESSAGE
# =====================================

async def build_crypto_message():

    # =================================
    # FETCH DATA
    # =================================

    coin_data = (
        await get_coin_market_data()
    )

    global_data = (
        await get_global_market_data()
    )

    fear_greed_data = (
        await get_fear_greed()
    )

    # =================================
    # COIN DATA VALIDATION
    # =================================

    if not coin_data:

        print(
            "⚠️ Coin market data unavailable."
        )

        return None

    # =================================
    # FEAR & GREED
    # =================================

    fear_greed_value = None
    fear_greed_classification = None

    if fear_greed_data:

        (
            fear_greed_value,
            fear_greed_classification,
        ) = format_fear_greed(
            fear_greed_data
        )

    # =================================
    # GLOBAL MARKET DATA
    # =================================

    total_market_cap = None
    total_volume = None
    btc_dominance = None

    try:

        global_root = (
            global_data.get(
                "data",
                {},
            )
            if global_data
            else {}
        )

        quotes = global_root.get(
            "quotes",
            {},
        )

        usd = quotes.get(
            "USD",
            {},
        )

        total_market_cap = usd.get(
            "total_market_cap_usd"
        )

        total_volume = usd.get(
            "total_24h_volume_usd"
        )

        btc_dominance = global_root.get(
            "bitcoin_percentage_of_market_cap"
        )

    except (
        TypeError,
        AttributeError,
    ):

        pass

    # =================================
    # MARKET SIGNAL
    # =================================

    (
        market_signal,
        average_change,
    ) = calculate_market_signal(
        coin_data,
        fear_greed_value,
    )

    # =================================
    # TIME
    # =================================

    now = datetime.now(
        timezone.utc
    )

    # Next scheduled update
    next_hour = (
        ((now.hour // 3) + 1) * 3
    )

    if next_hour >= 24:

        next_update = "00:00 UTC"

    else:

        next_update = (
            f"{next_hour:02d}:00 UTC"
        )

    # =================================
    # MESSAGE HEADER
    # =================================

    lines = [

        "📊 *NebuMine Pro BOT MARKET INTELLIGENCE*",
        "",
        f"🕐 {now.strftime('%H:%M')} UTC",
        "",
        "━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # =================================
    # COINS
    # =================================

    coin_lookup = {
        coin.get("id"): coin
        for coin in coin_data
    }

    for config in CRYPTO_COINS:

        coin = coin_lookup.get(
            config["id"]
        )

        if not coin:

            continue

        price = coin.get(
            "current_price"
        )

        market_cap = coin.get(
            "market_cap"
        )

        volume = coin.get(
            "total_volume"
        )

        change = coin.get(
            "price_change_percentage_24h"
        )

        lines.append(
            f"{config['symbol']} "
            f"*{config['name'].upper()}*"
        )

        lines.append(
            f"💵 {format_price(price)}"
        )

        lines.append(
            f"{format_percentage(change)} 24H"
        )

        lines.append(
            f"💎 Market Cap: "
            f"{format_large_number(market_cap)}"
        )

        lines.append(
            f"📊 Volume 24H: "
            f"{format_large_number(volume)}"
        )

        lines.append("")

    # =================================
    # GLOBAL MARKET
    # =================================

    lines.extend(
        [
            "━━━━━━━━━━━━━━━━━━",
            "",
            "🌐 *GLOBAL CRYPTO MARKET*",
            "",
            f"💎 Total Market Cap: "
            f"{format_large_number(total_market_cap)}",
            "",
            f"📊 Total Volume 24H: "
            f"{format_large_number(total_volume)}",
            "",
        ]
    )

    # =================================
    # BTC DOMINANCE
    # =================================

    if btc_dominance is not None:

        try:

            btc_dominance_text = (
                f"{float(btc_dominance):.2f}%"
            )

        except (
            TypeError,
            ValueError,
        ):

            btc_dominance_text = "N/A"

    else:

        btc_dominance_text = "N/A"

    lines.extend(
        [
            f"₿ BTC Dominance: "
            f"{btc_dominance_text}",
            "",
        ]
    )

    # =================================
    # FEAR & GREED
    # =================================

    if fear_greed_value is not None:

        lines.extend(
            [
                "━━━━━━━━━━━━━━━━━━",
                "",
                "😱 *FEAR & GREED*",
                "",
                f"📊 Score: "
                f"{fear_greed_value}/100",
                "",
                f"🧠 Sentiment: "
                f"{fear_greed_classification}",
                "",
            ]
        )

    # =================================
    # MARKET SIGNAL
    # =================================

    lines.extend(
        [
            "━━━━━━━━━━━━━━━━━━",
            "",
            "📈 *MARKET SIGNAL*",
            "",
            market_signal,
            "",
        ]
    )

    if average_change is not None:

        lines.append(
            f"📊 Average 24H move: "
            f"{average_change:+.2f}%"
        )

        lines.append("")

    # =================================
    # FOOTER
    # =================================

    lines.extend(
        [
            "━━━━━━━━━━━━━━━━━━",
            "",
            "📡 Live market data",
            f"⏭️ Next update: "
            f"{next_update}",
            "",
            "⚠️ Crypto markets are highly volatile.",
            "",
            "_Fear & Greed data: Alternative.me_",
            "_Market data: CoinGecko_",
        ]
    )

    return "\n".join(lines)


# =====================================
# BROADCAST JOB
# =====================================

async def crypto_broadcast_job(
    context: ContextTypes.DEFAULT_TYPE,
):

    if not CRYPTO_CHANNEL:

        print(
            "⚠️ CRYPTO_CHANNEL is not configured."
        )

        return

    try:

        message = (
            await build_crypto_message()
        )

        if not message:

            print(
                "⚠️ Crypto market message "
                "could not be generated."
            )

            return

        await context.bot.send_message(
            chat_id=CRYPTO_CHANNEL,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

        print(
            "✅ Version 2 crypto market "
            "broadcast sent successfully."
        )

    except Exception as exc:

        print(
            "❌ Version 2 crypto broadcast failed: "
            f"{exc}"
    )
