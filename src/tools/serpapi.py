"""Flight search — SerpAPI (neu con quota) + fallback link Google Flights/Shopping.

Khong muon bot chi show link ma khong co gia nhu truoc.
- Uu tien SerpAPI -> co gia + hang + gio bay
- Neu SerpAPI loi (het quota) -> fallback ve link Google Flights
"""

from __future__ import annotations

from datetime import date, timedelta
import httpx

from ..config import Config


def _get_next_friday() -> str:
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).isoformat()


CITY_MAP = {
    "SGN": "Sài Gòn", "HAN": "Hà Nội", "DAD": "Đà Nẵng",
    "PQC": "Phú Quốc", "CXR": "Nha Trang", "HUI": "Huế",
    "DIN": "Điện Biên", "VII": "Vinh", "UIH": "Quy Nhơn",
    "TBB": "Tuy Hòa", "VCA": "Cần Thơ", "NRT": "Tokyo Narita",
    "HND": "Tokyo Haneda", "KIX": "Osaka", "ICN": "Seoul",
    "BKK": "Bangkok", "SIN": "Singapore", "KUL": "Kuala Lumpur",
}

# ── SerpAPI ───────────────────────────────────────────────────────────

SERPAPI_BASE = "https://serpapi.com/search"


def _serpapi_search(params: dict) -> dict | None:
    """Call SerpAPI, return JSON or None on failure."""
    api_key = Config.serpapi_key
    if not api_key:
        return None
    try:
        params["api_key"] = api_key
        r = httpx.get(SERPAPI_BASE, params=params, timeout=15)
        data = r.json()
        if "error" in data:
            return None
        return data
    except Exception:
        return None


def _google_flights_link(
    dep: str, arr: str, out: str, ret: str, curr: str = "VND"
) -> str:
    return (
        f"https://www.google.com/travel/flights?"
        f"q=Flights+to+{arr}+from+{dep}+on+{out}+return+{ret}&curr={curr}"
    )


def _fallback_flights(
    dep_id: str, arr_id: str, out: str, ret: str, curr: str
) -> str:
    dep_name = CITY_MAP.get(dep_id, dep_id)
    arr_name = CITY_MAP.get(arr_id, arr_id)
    gf_link = _google_flights_link(dep_id, arr_id, out, ret, curr)
    lines = [
        f"✈️ *{dep_name} → {arr_name}*",
        f"📅 *{out}* → *{ret}*",
        "",
        "Xem giá mới nhất trên Google Flights:",
        f"👉 [Xem vé]({gf_link})",
    ]
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────

def search_flights(
    departure_id: str = "SGN",
    arrival_id: str = "DAD",
    outbound_date: str | None = None,
    return_date: str | None = None,
    adults: int = 1,
    currency: str = "VND",
) -> str:
    """Search flights — SerpAPI first, fallback Google Flights link."""
    dep = departure_id.upper()
    arr = arrival_id.upper()
    out = outbound_date or _get_next_friday()
    ret = return_date or (date.fromisoformat(out) + timedelta(days=5)).isoformat()

    dep_name = CITY_MAP.get(dep, dep)
    arr_name = CITY_MAP.get(arr, arr)

    # Try SerpAPI first
    data = _serpapi_search({
        "engine": "google_flights",
        "departure_id": dep,
        "arrival_id": arr,
        "outbound_date": out,
        "return_date": ret,
        "type": "1",  # round trip
        "adults": str(adults),
        "currency": currency,
    })

    if data is not None:
        best = data.get("best_flights", [])
        other = data.get("other_flights", [])
        all_flights = best + other

        if all_flights:
            lines = [f"✈️ *{dep_name} → {arr_name}*"]
            lines.append(f"📅 *{out}* → *{ret}* ({len(all_flights)} chuyến)")
            lines.append("")

            for i, f in enumerate(all_flights[:6], 1):
                price = f.get("price", "?")
                flights_data = f.get("flights", [])
                stops = "Thẳng" if len(flights_data) == 1 else f"{len(flights_data)-1} điểm dừng"
                emoji = ["🏆", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"][min(i - 1, 5)]
                lines.append(
                    f"{emoji} *{price:,}*" if isinstance(price, int)
                    else f"{emoji} *{price}*"
                )
                for seg in flights_data:
                    t_dep = seg.get("departure_airport", {}).get("time", "?")[11:16]
                    t_arr = seg.get("arrival_airport", {}).get("time", "?")[11:16]
                    al = seg.get("airline", "?")
                    fn = seg.get("flight_number", "")
                    dur = seg.get("duration", 0)
                    lines.append(f"   {t_dep}→{t_arr} ({dur}ph) {al} {fn}")
                lines.append("")

            gf_link = _google_flights_link(dep, arr, out, ret, currency)
            lines.append(f"👉 [Xem thêm trên Google Flights]({gf_link})")
            return "\n".join(lines)

    # Fallback
    return _fallback_flights(dep, arr, out, ret, currency)


def search_shopping(query: str, currency: str = "VND") -> str:
    """Search shopping — SerpAPI first, fallback Google Shopping link."""
    import urllib.parse

    # Try SerpAPI first
    data = _serpapi_search({
        "engine": "google_shopping",
        "q": query,
    })

    if data is not None:
        results = data.get("shopping_results", [])
        if results:
            lines = [f"🛒 *{query}* ({len(results)} kết quả)"]
            for i, r in enumerate(results[:6], 1):
                title = r.get("title", "?")
                price = r.get("price", "?")
                source = r.get("source", "")
                rating = r.get("rating", "")
                reviews = r.get("reviews", "")
                emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"][min(i - 1, 5)]
                line = f"{emoji} {title}"
                if price:
                    line += f" 💰 *{price}*"
                if source:
                    line += f" — {source}"
                if rating:
                    line += f" ⭐{rating}"
                    if reviews:
                        line += f" ({reviews} đánh giá)"
                lines.append(line)
            return "\n".join(lines)

    # Fallback
    q = urllib.parse.quote(query)
    gs_link = f"https://www.google.com/search?tbm=shop&q={q}"
    return f"🛒 *{query}*\n\n👉 [Xem trên Google Shopping]({gs_link})"
