import requests


def get_prices():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum,tether,usd-coin"
        "&vs_currencies=usd"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        return {
            "BTC": data["bitcoin"]["usd"],
            "ETH": data["ethereum"]["usd"],
            "USDT TRC20": data["tether"]["usd"],
            "USDT ERC20": data["tether"]["usd"],
            "USDC ERC20": data["usd-coin"]["usd"],
        }

    except Exception as e:
        print("Price API Error:", e)

        return {
            "BTC": None,
            "ETH": None,
            "USDT TRC20": None,
            "USDT ERC20": None,
            "USDC ERC20": None,
      }
