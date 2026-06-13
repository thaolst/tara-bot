"""Flight search — không dùng SerpAPI, chỉ generate Google Flights/Shopping link.

Thay thế SerpAPI free (250/thang) bang link truc tiep:
- Google Flights: route + date → link
- Google Shopping: query → link
- Không ton API, không gioi han, không quota.
"""

from __future__ import annotations

from datetime import date, timedelta


def _get_next_friday() -> str:
    """Return next Friday as YYYY-MM-DD."""
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7  # Friday = 4
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


def search_flights(
    departure_id: str = "SGN",
    arrival_id: str = "DAD",
    outbound_date: str | None = None,
    return_date: str | None = None,
    adults: int = 1,
    currency: str = "VND",
) -> str:
    """Generate Google Flights search link — no API call.

    Args:
        departure_id: IATA code (e.g. SGN, HAN, DAD)
        arrival_id: IATA code of destination
        outbound_date: YYYY-MM-DD, defaults to next Friday
        return_date: YYYY-MM-DD, defaults to outbound + 5 days
        adults: number of passengers
        currency: VND, USD, etc.

    Returns:
        Formatted message with Google Flights link
    """
    outbound = outbound_date or _get_next_friday()
    ret = return_date or (
        date.fromisoformat(outbound) + timedelta(days=5)
    ).isoformat()

    dep_name = CITY_MAP.get(departure_id, departure_id)
    arr_name = CITY_MAP.get(arrival_id, arrival_id)

    # Build Google Flights URL
    gf_link = (
        f"https://www.google.com/travel/flights?"
        f"q=Flights+to+{arrival_id}+from+{departure_id}"
        f"+on+{outbound}+return+{ret}"
        f"&curr={currency}"
    )

    lines = [
        f"✈️ *{dep_name} → {arr_name}*",
        f"📅 *{outbound}* → *{ret}*",
        "",
        "Mở link này để xem giá vé mới nhất:",
        f"👉 [Xem trên Google Flights]({gf_link})",
        "",
        "💡 *Mẹo:* Dùng filter sắp xếp theo giá thấp nhất "
        "hoặc thời gian bay ngắn nhất để chọn chuyến phù hợp.",
        "",
        "Hoặc bạn có thể đặt trực tiếp trên:",
        f"• [VietJet Air](https://www.vietjetair.com)",
        f"• [Vietnam Airlines](https://www.vietnamairlines.com)",
        f"• [Bamboo Airways](https://www.bambooairways.com)",
    ]

    if dep_name != arr_name:
        lines.insert(3, f"🚀 *Khoảng cách:* {dep_name} → {arr_name}")

    return "\n".join(lines)


def search_shopping(query: str, currency: str = "VND") -> str:
    """Generate Google Shopping search link — no API call.

    Args:
        query: product name to search
        currency: currency code

    Returns:
        Formatted message with Google Shopping link
    """
    import urllib.parse
    q_encoded = urllib.parse.quote(query)

    gs_link = f"https://www.google.com/search?tbm=shop&q={q_encoded}&curr={currency}"

    lines = [
        f"🛒 *{query}*",
        "",
        "Mở link này để so sánh giá:",
        f"👉 [Xem trên Google Shopping]({gs_link})",
        "",
        "💡 *Mẹo:* Lọc theo khoảng giá, đánh giá, hoặc chọn "
        "'Miễn phí vận chuyển' để tìm deal tốt nhất.",
    ]

    return "\n".join(lines)
