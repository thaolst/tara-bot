"""Flight search tool using SerpAPI."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

import httpx

from ..config import Config


def _get_next_friday() -> str:
    """Return next Friday as YYYY-MM-DD."""
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7  # Friday = 4
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).isoformat()


SERPAPI_BASE = "https://serpapi.com/search.json"


def search_flights(
    departure_id: str = "SGN",
    arrival_id: str = "HAN",
    outbound_date: str | None = None,
    return_date: str | None = None,
    adults: int = 1,
    currency: str = "VND",
) -> str:
    """Search flights via SerpAPI Google Flights engine.

    Args:
        departure_id: IATA code (e.g. SGN, HAN, DAD)
        arrival_id: IATA code of destination
        outbound_date: YYYY-MM-DD, defaults to next Friday
        return_date: YYYY-MM-DD, defaults to outbound + 5 days
        adults: number of passengers
        currency: VND, USD, etc.

    Returns:
        Formatted string with best options + affiliate link
    """
    key = Config.serpapi_key
    outbound = outbound_date or _get_next_friday()
    ret = return_date or (
        date.fromisoformat(outbound) + timedelta(days=5)
    ).isoformat()

    params: dict[str, Any] = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound,
        "return_date": ret,
        "adults": adults,
        "currency": currency,
        "api_key": key,
    }

    try:
        resp = httpx.get(SERPAPI_BASE, params=params, timeout=30)
        data = resp.json()
    except httpx.TimeoutException:
        return "⚠️ SerpAPI timeout (>30s). Thu lai sau it phut."
    except Exception as e:
        return f"⚠️ Loi ket noi SerpAPI: {type(e).__name__}: {e}"

    # SerpAPI tra loi trong body ke ca khi status 200
    if "error" in data:
        err = data["error"]
        if "run out of searches" in err.lower() or "quota" in err.lower():
            return "⚠️ SerpAPI het quota thang nay. Check serpapi.com/dashboard."
        if "invalid api key" in err.lower():
            return "⚠️ SERPAPI_KEY khong hop le. Check fly secrets."
        return f"⚠️ SerpAPI error: {err}"

    if resp.status_code != 200:
        return f"⚠️ SerpAPI HTTP {resp.status_code}: {resp.text[:200]}"

    return _format_flights(data, departure_id, arrival_id, outbound, ret)


def _format_flights(
    data: dict, dep: str, arr: str, out: str, ret: str
) -> str:
    """Format flight results into compact, beautiful Telegram message."""
    best = data.get("best_flights", [])
    other = data.get("other_flights", [])
    all_flights = best + other

    if not all_flights:
        return "😕 Không tìm thấy chuyến bay nào cho tuyến này."

    # Parse IATA → city name
    city_map = {"SGN": "Sài Gòn", "HAN": "Hà Nội", "DAD": "Đà Nẵng",
                "PQC": "Phú Quốc", "CXR": "Nha Trang", "HUI": "Huế",
                "DIN": "Điện Biên", "VII": "Vinh", "UIH": "Quy Nhơn",
                "TBB": "Tuy Hòa", "VCA": "Cần Thơ"}
    dep_name = city_map.get(dep, dep)
    arr_name = city_map.get(arr, arr)

    # Emoji for header
    lines = [f"✈️ *{dep_name} → {arr_name}*"]
    lines.append(f"📅 *{out}* → *{ret}* ({len(all_flights)} chuyến)")
    lines.append("")

    # Google Flights search link
    gf_link = (
        f"https://www.google.com/travel/flights?"
        f"q=Flights+to+{arr}+from+{dep}+on+{out}+return+{ret}"
    )

    for i, flight in enumerate(all_flights[:5], 1):
        price = flight.get('price', 0)
        price_fmt = f"{price:,}đ" if price < 1000000 else f"{price/1000:,.0f}K"

        legs = flight.get("flights", [])
        total_min = flight.get("total_duration", 0)
        h, m = divmod(total_min, 60)
        duration = f"{h}h{m}" if h else f"{m}ph"

        # Build compact per-flight block
        stops = []
        segments = []
        for leg in legs:
            airline = leg.get("airline", "?")
            dep_t = leg.get("departure_airport", {}).get("time", "").split()[-1][:5]
            arr_t = leg.get("arrival_airport", {}).get("time", "").split()[-1][:5]
            dep_code = leg.get("departure_airport", {}).get("id", "")
            arr_code = leg.get("arrival_airport", {}).get("id", "")
            flight_no = leg.get("flight_number", "")
            segments.append(f"{dep_t}→{arr_t}")
            stops.append(f"{airline} {flight_no}")

        layovers = flight.get("layovers", [])
        layover_names = [l.get("name", str(l)) if isinstance(l, dict) else str(l) for l in layovers]
        stop_text = f" · ⏳ {', '.join(layover_names)}" if layover_names else " · *Thẳng*"

        # Price rank emoji
        rank_emoji = ["🏆", "🥈", "🥉", "4️⃣", "5️⃣"][min(i - 1, 4)]

        # One-line status: airline + flight_no
        airline_line = " → ".join(stops)

        lines.append(
            f"{rank_emoji} *{price_fmt}* {' → '.join(segments)} ({duration})"
        )
        lines.append(f"   `{airline_line}`{stop_text}")
        lines.append("")

    # Footer: Google Flights link + note
    lines.append(f"[🔍 Xem thêm trên Google Flights]({gf_link})")

    return "\n".join(lines)


def search_shopping(query: str, currency: str = "VND") -> str:
    """Search products via SerpAPI Google Shopping engine.

    Args:
        query: product name to search
        currency: currency for prices

    Returns:
        Formatted product listing with prices, ratings, links
    """
    key = Config.serpapi_key
    params: dict[str, Any] = {
        "engine": "google_shopping",
        "q": query,
        "currency": currency,
        "api_key": key,
    }

    try:
        resp = httpx.get(SERPAPI_BASE, params=params, timeout=30)
        data = resp.json()
    except httpx.TimeoutException:
        return "⚠️ SerpAPI timeout (>30s). Thu lai sau it phut."
    except Exception as e:
        return f"⚠️ Loi ket noi SerpAPI: {type(e).__name__}: {e}"

    if "error" in data:
        err = data["error"]
        if "run out of searches" in err.lower() or "quota" in err.lower():
            return "⚠️ SerpAPI het quota thang nay. Check serpapi.com/dashboard."
        if "invalid api key" in err.lower():
            return "⚠️ SERPAPI_KEY khong hop le. Check fly secrets."
        return f"⚠️ SerpAPI error: {err}"

    if resp.status_code != 200:
        return f"⚠️ SerpAPI HTTP {resp.status_code}: {resp.text[:200]}"

    results = data.get("shopping_results", [])
    if not results:
        return f"😕 Không tìm thấy \"{query}\"."

    lines = [f"🛒 *{query}* ({len(results)} kết quả)", ""]

    # Currency symbol mapping
    currency_symbols = {"VND": "₫", "USD": "$", "SGD": "S$", "JPY": "¥"}

    for i, item in enumerate(results[:6], 1):
        title = item.get("title", "?")
        price = item.get("price", "?")
        source = item.get("source", "?")
        rating = item.get("rating")
        reviews = item.get("reviews", 0)
        delivery = item.get("delivery", "")
        link = item.get("product_link") or item.get("link", "")

        # Rank emoji
        rank = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"][min(i - 1, 5)]

        # Price highlight
        is_cheapest = i == 1
        price_fmt = f"*{price}* 🔥" if is_cheapest and i <= 3 else f"*{price}*"

        # Rating stars
        stars = ""
        if rating:
            full = int(rating)
            stars = "⭐" * full + f" {rating}" if full > 0 else f"⭐ {rating}"
            if reviews:
                stars += f" ({reviews:,} đánh giá)"

        # Delivery info
        delivery_tag = f" · 🚚 {delivery}" if delivery else ""

        lines.append(f"{rank} {title}")
        lines.append(f"   💰 {price_fmt} — {source}{delivery_tag}")
        if stars:
            lines.append(f"   {stars}")
        if link:
            lines.append(f"   🔗 {link}")
        lines.append("")

    return "\n".join(lines)
