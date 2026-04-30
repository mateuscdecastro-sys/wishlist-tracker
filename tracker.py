import json
import os
import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

CONFIG_FILE = "config.json"
PRICES_FILE = "prices.json"


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_prices():
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE) as f:
            return json.load(f)
    return {}


def save_prices(prices):
    with open(PRICES_FILE, "w") as f:
        json.dump(prices, f, indent=2)


def load_cookies():
    raw = os.environ.get("AMAZON_COOKIES")
    if not raw:
        print("ERROR: AMAZON_COOKIES env var not set")
        sys.exit(1)
    # Cookie-Editor exports a JSON array of {name, value, ...} dicts
    return {c["name"]: c["value"] for c in json.loads(raw)}


def send_notification(topic, title, message, priority="default"):
    try:
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": priority},
            timeout=10,
        )
    except Exception as e:
        print(f"Notification failed: {e}")


def fetch_wishlist(url, cookies):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, cookies=cookies, headers=headers, timeout=30)
    if "ap/signin" in resp.url or "ap/signin" in resp.text[:2000]:
        return None, "session_expired"
    return resp.text, None


def parse_items(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for li in soup.select("li[data-itemId]"):
        item_id = li.get("data-itemId", "")

        name_el = (
            li.select_one(f"#itemName_{item_id}")
            or li.select_one("a[id^='itemName_']")
            or li.select_one("span[id^='itemName_']")
        )
        name = name_el.get_text(strip=True) if name_el else "Unknown item"

        # ASIN from product link
        asin = item_id  # fallback
        link_el = li.select_one("a[href*='/dp/']")
        if link_el:
            m = re.search(r"/dp/([A-Z0-9]{10})", link_el.get("href", ""))
            if m:
                asin = m.group(1)

        # Price: data-price attribute is most reliable
        price = None
        data_price = li.get("data-price")
        if data_price and data_price not in ("-Infinity", "Infinity", ""):
            try:
                price = float(data_price)
            except ValueError:
                pass

        if price is None:
            price_el = li.select_one(
                f"#itemPrice_{item_id} .a-offscreen"
            ) or li.select_one(".a-price .a-offscreen")
            if price_el:
                text = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                try:
                    price = float(text)
                except ValueError:
                    pass

        if price is not None and price > 0:
            items.append({"asin": asin, "name": name, "price": price})

    return items


def check_and_notify(items, prices, threshold, topic):
    today = str(date.today())
    for item in items:
        asin = item["asin"]
        price = item["price"]
        name = item["name"]

        if asin not in prices:
            prices[asin] = {
                "name": name,
                "baseline": price,
                "history": [{"date": today, "price": price}],
            }
            print(f"New item tracked: {name} @ ${price:.2f}")
            continue

        record = prices[asin]
        record["name"] = name
        record["history"].append({"date": today, "price": price})

        baseline = record["baseline"]
        drop = (baseline - price) / baseline if baseline > 0 else 0
        print(f"{name}: ${price:.2f} (baseline ${baseline:.2f}, {drop:.1%} drop)")

        if drop >= threshold:
            send_notification(
                topic,
                title=f"Price drop on wishlist item!",
                message=(
                    f"{name[:80]}\n"
                    f"Was ${baseline:.2f} → now ${price:.2f} ({drop:.0%} off)\n"
                    f"https://www.amazon.com/dp/{asin}"
                ),
                priority="high",
            )
            print(f"  ✓ Notification sent ({drop:.0%} drop)")


def main():
    config = load_config()
    prices = load_prices()
    cookies = load_cookies()

    url = config["wishlist_url"]
    topic = config["ntfy_topic"]
    threshold = config.get("threshold", 0.40)

    print(f"Fetching: {url}")
    html, error = fetch_wishlist(url, cookies)

    if error == "session_expired":
        send_notification(
            topic,
            title="Amazon cookies expired",
            message=(
                "Your Amazon session has expired.\n"
                "Export fresh cookies and update the AMAZON_COOKIES GitHub Secret."
            ),
            priority="urgent",
        )
        print("Session expired — notified via ntfy")
        sys.exit(0)

    items = parse_items(html)
    print(f"Found {len(items)} priced items")

    if not items:
        print("WARNING: No items found. Wishlist may be empty or page structure changed.")
        sys.exit(0)

    check_and_notify(items, prices, threshold, topic)
    save_prices(prices)
    print("Done.")


if __name__ == "__main__":
    main()
