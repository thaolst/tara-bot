"""Xem ngay gio tot theo Am Lich - Can Chi ngay, gio Hoang Dao, xung hop tuoi.

Logic:
- Can Chi ngay: tinh tu epoch Am Lich (can/chi lap lai theo chu ky 60)
- Gio Hoang Dao / Hac Dao: theo chi ngay, moi ngay co 6 gio tot / 6 gio xau (co dinh)
- Xung / Hop voi tuoi user: so sanh chi tuoi vs chi ngay
- Khong phu thuoc external API, tinh thuan toan bo offline
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import NamedTuple


# -- Can / Chi ----------------------------------------------------------

CAN = ["Giap", "At", "Binh", "Dinh", "Mau", "Ky", "Canh", "Tan", "Nham", "Quy"]
CHI = ["Ty", "Suu", "Dan", "Mao", "Thin", "Ti", "Ngo", "Mui", "Than", "Dau", "Tuat", "Hoi"]

# Emoji tuong trung cho 12 chi
CHI_ANIMAL = {
    "Ty": "🐭", "Suu": "🐂", "Dan": "🐯", "Mao": "🐰",
    "Thin": "🐉", "Ti": "🐍", "Ngo": "🐴", "Mui": "🐑",
    "Than": "🐒", "Dau": "🐓", "Tuat": "🐕", "Hoi": "🐗",
}

# Anchor: 01/01/2000 duong lich = Can Chi ngay Giap Thin (index can=0, chi=4)
_ANCHOR_DATE = date(2000, 1, 1)
_ANCHOR_CAN = 0   # Giap
_ANCHOR_CHI = 4   # Thin


def _can_chi_of_date(d: date) -> tuple[str, str]:
    delta = (d - _ANCHOR_DATE).days
    can_idx = (_ANCHOR_CAN + delta) % 10
    chi_idx = (_ANCHOR_CHI + delta) % 12
    return CAN[can_idx], CHI[chi_idx]


# -- Gio Hoang Dao / Hac Dao -------------------------------------------
# Theo Chi ngay, 12 gio (Ty=23-1h, Suu=1-3h, ...) xen ke tot/xau
# Bang: moi hang = chi ngay, 12 gio = T (tot) hoac X (xau)
# Nguon: Lich Van Nien truyen thong

_GIO_TABLE: dict[str, list[str]] = {
    # chi ngay: [Ty, Suu, Dan, Mao, Thin, Ti, Ngo, Mui, Than, Dau, Tuat, Hoi]
    "Ty":   ["T","X","T","X","T","X","T","X","T","X","T","X"],
    "Suu":  ["X","T","X","T","X","T","X","T","X","T","X","T"],
    "Dan":  ["T","X","T","X","T","X","T","X","T","X","T","X"],
    "Mao":  ["X","T","X","T","X","T","X","T","X","T","X","T"],
    "Thin": ["T","X","T","X","T","X","T","X","T","X","T","X"],
    "Ti":   ["X","T","X","T","X","T","X","T","X","T","X","T"],
    "Ngo":  ["T","X","T","X","T","X","T","X","T","X","T","X"],
    "Mui":  ["X","T","X","T","X","T","X","T","X","T","X","T"],
    "Than": ["T","X","T","X","T","X","T","X","T","X","T","X"],
    "Dau":  ["X","T","X","T","X","T","X","T","X","T","X","T"],
    "Tuat": ["T","X","T","X","T","X","T","X","T","X","T","X"],
    "Hoi":  ["X","T","X","T","X","T","X","T","X","T","X","T"],
}

# Theo Lich Van Nien chinh xac hon - bang Hoang Dao theo Chi ngay
# 6 gio Hoang Dao (tot) cho moi Chi ngay
_HOANG_DAO_GIO: dict[str, list[str]] = {
    "Ty":   ["Suu", "Mao", "Ngo", "Than", "Dau", "Hoi"],
    "Suu":  ["Dan", "Thin", "Mui", "Dau", "Tuat", "Ty"],
    "Dan":  ["Mao", "Ti", "Than", "Tuat", "Hoi", "Suu"],
    "Mao":  ["Thin", "Ngo", "Dau", "Hoi", "Ty", "Dan"],
    "Thin": ["Ti", "Mui", "Tuat", "Ty", "Suu", "Mao"],
    "Ti":   ["Ngo", "Than", "Hoi", "Suu", "Dan", "Thin"],
    "Ngo":  ["Mui", "Dau", "Ty", "Dan", "Mao", "Ti"],
    "Mui":  ["Than", "Tuat", "Suu", "Mao", "Thin", "Ngo"],
    "Than": ["Dau", "Hoi", "Dan", "Thin", "Ti", "Mui"],
    "Dau":  ["Tuat", "Ty", "Mao", "Ti", "Ngo", "Than"],
    "Tuat": ["Hoi", "Suu", "Thin", "Ngo", "Mui", "Dau"],
    "Hoi":  ["Ty", "Dan", "Ti", "Mui", "Than", "Tuat"],
}

# Gio Chi -> khoang gio thuc (gio bat dau, gio ket thuc)
_CHI_GIO_RANGE: dict[str, tuple[int, int]] = {
    "Ty":   (23, 1),
    "Suu":  (1, 3),
    "Dan":  (3, 5),
    "Mao":  (5, 7),
    "Thin": (7, 9),
    "Ti":   (9, 11),
    "Ngo":  (11, 13),
    "Mui":  (13, 15),
    "Than": (15, 17),
    "Dau":  (17, 19),
    "Tuat": (19, 21),
    "Hoi":  (21, 23),
}


def _lucky_hours(chi_ngay: str) -> list[dict]:
    """Tra ve cac gio Hoang Dao trong ngay co chi_ngay."""
    good_chis = _HOANG_DAO_GIO.get(chi_ngay, [])
    result = []
    for chi in good_chis:
        r = _CHI_GIO_RANGE[chi]
        start = r[0]
        end = r[1]
        if start == 23:
            time_str = "23:00 - 01:00"
        else:
            time_str = f"{start:02d}:00 - {end:02d}:00"
        result.append({
            "chi": chi,
            "animal": CHI_ANIMAL[chi],
            "time": time_str,
        })
    return result


# -- Xung / Hop theo tuoi ----------------------------------------------
# Luc Hop (hop tot): Ty-Suu, Dan-Hoi, Mao-Tuat, Thin-Dau, Ti-Than, Ngo-Mui
_LUC_HOP: dict[str, str] = {
    "Ty": "Suu", "Suu": "Ty",
    "Dan": "Hoi", "Hoi": "Dan",
    "Mao": "Tuat", "Tuat": "Mao",
    "Thin": "Dau", "Dau": "Thin",
    "Ti": "Than", "Than": "Ti",
    "Ngo": "Mui", "Mui": "Ngo",
}

# Luc Xung (xung xau): Ty-Ngo, Suu-Mui, Dan-Than, Mao-Dau, Thin-Tuat, Ti-Hoi
_LUC_XUNG: dict[str, str] = {
    "Ty": "Ngo", "Ngo": "Ty",
    "Suu": "Mui", "Mui": "Suu",
    "Dan": "Than", "Than": "Dan",
    "Mao": "Dau", "Dau": "Mao",
    "Thin": "Tuat", "Tuat": "Thin",
    "Ti": "Hoi", "Hoi": "Ti",
}

# Tam Hop (hop tot nhat): Ty-Thin-Than, Suu-Ti-Dau, Dan-Ngo-Tuat, Mao-Mui-Hoi
_TAM_HOP: list[set] = [
    {"Ty", "Thin", "Than"},
    {"Suu", "Ti", "Dau"},
    {"Dan", "Ngo", "Tuat"},
    {"Mao", "Mui", "Hoi"},
]


def _chi_of_birth_year(birth_year: int) -> str:
    """Chi cua nam sinh (tinh don gian: 2000=Thin la anchor)."""
    chi_idx = (birth_year - 2000 + 4) % 12  # 2000=Thin=index 4
    return CHI[chi_idx]


def _relation(chi_tuoi: str, chi_ngay: str) -> str:
    """Moi quan he giua chi tuoi user vs chi ngay."""
    if chi_tuoi == chi_ngay:
        return "hoa"  # cung chi - binh thuong
    if _LUC_HOP.get(chi_tuoi) == chi_ngay:
        return "hop"
    if _LUC_XUNG.get(chi_tuoi) == chi_ngay:
        return "xung"
    for group in _TAM_HOP:
        if chi_tuoi in group and chi_ngay in group:
            return "tam_hop"
    return "binh"


# -- Ngay Hoang Dao (theo lich truyen thong) ---------------------------
# 12 ngay Hoang Dao trong thang Am Lich: 1,7,8,14,15,21,22,27,28 ... 
# Don gian hoa: dung Chi ngay de phan loai ngay tot/xau theo "Nhat Luc Ky"
# Ngay can "Giap, At, Binh, Dinh" (can 0-3) la ngay co nang luong duong
_GOOD_CAN = {"Giap", "At", "Binh", "Dinh", "Canh", "Tan"}

# Chi ngay tot cho di chuyen / xuat hanh
_GOOD_CHI_TRAVEL = {"Mao", "Thin", "Ngo", "Than", "Hoi"}
_BAD_CHI_TRAVEL = {"Ty", "Suu", "Ti", "Dau", "Tuat", "Mui"}  # can than hon


def _day_score(can: str, chi: str, chi_tuoi: str) -> int:
    """Tinh diem tong hop cho ngay (0-100)."""
    score = 50
    if can in _GOOD_CAN:
        score += 10
    if chi in _GOOD_CHI_TRAVEL:
        score += 15
    elif chi in _BAD_CHI_TRAVEL:
        score -= 10

    rel = _relation(chi_tuoi, chi)
    score_map = {"tam_hop": 25, "hop": 20, "binh": 0, "hoa": 5, "xung": -25}
    score += score_map.get(rel, 0)

    return max(0, min(100, score))


# -- Public API --------------------------------------------------------

class DayInfo(NamedTuple):
    date_str: str       # YYYY-MM-DD
    weekday: str        # Thu 2, Thu 3, ...
    can: str
    chi: str
    score: int          # 0-100
    relation: str       # hop / tam_hop / xung / binh / hoa
    lucky_hours: list[dict]
    note: str


_WEEKDAY_VN = ["Thu 2", "Thu 3", "Thu 4", "Thu 5", "Thu 6", "Thu 7", "Chu Nhat"]


def get_lucky_dates(
    birth_date: str = "",
    from_date: str | None = None,
    days: int = 14,
    birth_dates: str | list[str] | None = None,
) -> str:
    """
    Tinh ngay gio tot cho 1 hoac nhieu nguoi dua tren ngay sinh.

    Args:
        birth_date: Ngay sinh YYYY-MM-DD hoac YYYY (cho 1 nguoi)
        from_date:  Bat dau xem tu ngay nao (YYYY-MM-DD), mac dinh hom nay
        days:       So ngay xem phia truoc (mac dinh 14)
        birth_dates: List ngay sinh cho nhieu nguoi (vd: ["1995", "1965", "1968"])

    Returns:
        Formatted string cho Telegram.
    """
    start = date.fromisoformat(from_date) if from_date else date.today()
    
    # Collect all birth dates into a list
    bdates: list[str] = []
    if birth_dates:
        if isinstance(birth_dates, str):
            # Handle comma-separated or newline-separated
            bdates = [b.strip() for b in birth_dates.replace("\n", ",").split(",") if b.strip()]
        else:
            bdates = list(birth_dates)
    elif birth_date:
        bdates = [birth_date]
    
    if not bdates:
        return "Vui long nhap ngay sinh (birth_date) hoac danh sach ngay sinh (birth_dates)."
    
    # Parse birth dates and get unique chi
    chi_users: list[tuple[int, str, str, str]] = []  # (birth_year, chi, animal, label)
    for bd in bdates:
        try:
            if len(bd) == 4:
                birth_year = int(bd)
            else:
                birth_year = date.fromisoformat(bd).year
        except Exception:
            # Try partial date "MM-DD" - use current year
            try:
                from datetime import datetime
                birth_year = datetime.strptime(bd, "%m-%d").replace(year=start.year).year
            except Exception:
                continue
        
        chi = _chi_of_birth_year(birth_year)
        animal = CHI_ANIMAL[chi]
        
        # Create label
        year_label = bd if len(bd) == 4 else bd
        chi_users.append((birth_year, chi, animal, year_label))
    
    if not chi_users:
        return "Khong doc duoc ngay sinh nao."
    
    # For a single user, use the original format
    if len(chi_users) == 1:
        return _compute_and_format(start, days, chi_users[0])
    
    # For multiple users, compute combined results
    return _compute_and_format_multi(start, days, chi_users)


def _compute_and_format(start: date, days: int, user_info: tuple) -> str:
    """Compute and format for a single user."""
    birth_year, chi_tuoi, animal, _ = user_info
    results: list[DayInfo] = []
    for i in range(days):
        d = start + timedelta(days=i)
        can, chi = _can_chi_of_date(d)
        score = _day_score(can, chi, chi_tuoi)
        rel = _relation(chi_tuoi, chi)
        lucky_hrs = _lucky_hours(chi)
        wd = _WEEKDAY_VN[d.weekday()]
        note = _build_note(can, chi, [rel], score)
        results.append(DayInfo(
            date_str=d.isoformat(),
            weekday=wd,
            can=can, chi=chi,
            score=score,
            relation=rel,
            lucky_hours=lucky_hrs,
            note=note,
        ))
    return _format_output(results, chi_tuoi, animal)


def _compute_and_format_multi(start: date, days: int, chi_users: list) -> str:
    """Compute and format for multiple users, finding common good days."""
    results: list[dict] = []
    
    for i in range(days):
        d = start + timedelta(days=i)
        can, chi = _can_chi_of_date(d)
        
        # Compute scores for all users
        user_scores = []
        total_score = 0
        for birth_year, chi_tuoi, animal, label in chi_users:
            score = _day_score(can, chi, chi_tuoi)
            rel = _relation(chi_tuoi, chi)
            user_scores.append({"chi": chi_tuoi, "animal": animal, "score": score, "rel": rel, "label": label})
            total_score += score
        
        avg_score = total_score // len(chi_users)
        rels = [u["rel"] for u in user_scores]
        lucky_hrs = _lucky_hours(chi)
        wd = _WEEKDAY_VN[d.weekday()]
        note = _build_note(can, chi, rels, avg_score)
        
        results.append({
            "date_str": d.isoformat(),
            "weekday": wd,
            "can": can,
            "chi": chi,
            "animal": CHI_ANIMAL[chi],
            "score": avg_score,
            "user_scores": user_scores,
            "lucky_hours": lucky_hrs[:3],
            "note": note,
        })
    
    return _format_output_multi(results, chi_users)


def _format_output_multi(results: list[dict], chi_users: list) -> str:
    """Format combined lucky dates for multiple users."""
    labels = [f"tuoi {u[2]} {u[1]}" for u in chi_users]
    lines = []
    lines.append(f"Xem ngay tot cho: {', '.join(labels)}")
    lines.append(f"Xem {len(results)} ngay")
    lines.append("")
    
    # Filter good days
    good = [r for r in results if r["score"] >= 65]
    good.sort(key=lambda r: r["score"], reverse=True)
    
    if good:
        lines.append("Cac ngay tot nhat cho ca nha:")
        lines.append("")
        for r in good[:5]:
            bar = _score_bar(r["score"])
            lines.append(f"{r['date_str']} ({r['weekday']}) - {r['can']} {r['chi']} {r['animal']}")
            lines.append(f"  [{bar}] {r['score']}/100")
            
            # Per-user breakdown
            for us in r["user_scores"]:
                rel_icon = {"tam_hop": "✅", "hop": "✅", "binh": "➖", "hoa": "➖", "xung": "❌"}
                icon = rel_icon.get(us["rel"], "➖")
                lines.append(f"    {icon} {us['label']}: {us['score']}/100")
            
            if r["lucky_hours"]:
                gio_list = ", ".join(
                    f"{g['chi']} {g['animal']} ({g['time']})"
                    for g in r["lucky_hours"]
                )
                lines.append(f"  Gio Hoang Dao: {gio_list}")
            lines.append("")
    else:
        lines.append("Khong co ngay tot cho ca nha trong thoi gian nay.")
    
    return "\n".join(lines)


def get_lucky_dates_group(
    birth_dates: list[str],
    from_date: str | None = None,
    days: int = 14,
) -> str:
    """Xem ngay tot cho nhom (2-5 nguoi). Tu choi ngay nao xung voi bat ky ai."""
    return get_lucky_dates(
        birth_dates=birth_dates,
        from_date=from_date,
        days=days,
    )


def _build_note(can: str, chi: str, rels: list[str], score: int) -> str:
    rel_text = {
        "tam_hop": "Tam Hop - rat tot",
        "hop": "Luc Hop - tot",
        "hoa": "Cung chi - binh thuong",
        "binh": "Binh thuong",
        "xung": "Luc Xung - tranh di chuyen neu co the",
    }
    if score >= 80:
        prefix = "Ngay rat tot"
    elif score >= 65:
        prefix = "Ngay tot"
    elif score >= 50:
        prefix = "Ngay binh thuong"
    elif score >= 35:
        prefix = "Nen can nhac"
    else:
        prefix = "Tranh neu duoc"

    rel_priority = ["xung", "binh", "hoa", "hop", "tam_hop"]
    worst_rel = min(rels, key=lambda r: rel_priority.index(r)) if rels else "binh"
    base = rel_text.get(worst_rel, "")
    return f"{prefix}. {base}".strip(". ")


def _score_bar(score: int) -> str:
    filled = round(score / 10)
    return "█" * filled + "░" * (10 - filled)


def _format_output(days: list[DayInfo], chi_tuoi: str, animal: str) -> str:
    lines = []
    lines.append(f"Tu vi xuat hanh cho tuoi {chi_tuoi} {animal}")
    lines.append("")

    # Loc ngay tot (score >= 65) va sort
    good_days = [d for d in days if d.score >= 65]
    all_days = days

    if not good_days:
        lines.append("Trong " + str(len(days)) + " ngay toi khong co ngay qua tot.")
        lines.append("Chon ngay co diem cao nhat ben duoi.")

    lines.append(f"Xem {len(all_days)} ngay tu {all_days[0].date_str} den {all_days[-1].date_str}")
    lines.append("")

    # Hien thi tat ca, highlight ngay tot
    for d in all_days:
        bar = _score_bar(d.score)
        is_good = d.score >= 65
        star = "OK" if is_good else "  "
        lines.append(
            f"{star} {d.date_str} ({d.weekday}) - {d.can} {d.chi} {CHI_ANIMAL[d.chi]}"
        )
        lines.append(f"   [{bar}] {d.score}/100 - {d.note}")

        if is_good:
            gio_list = ", ".join(
                f"{g['chi']} {g['animal']} ({g['time']})"
                for g in d.lucky_hours[:3]  # chi hien 3 gio dau
            )
            lines.append(f"   Gio Hoang Dao: {gio_list}")
        lines.append("")

    # Goi y tom tat
    top3 = sorted(good_days, key=lambda x: x.score, reverse=True)[:3]
    if top3:
        lines.append("Top ngay nen chon:")
        for d in top3:
            lines.append(
                f"  - {d.date_str} ({d.weekday}) diem {d.score}/100"
            )
        lines.append("")
        lines.append("Hoi them gio cu the de xem gio tot trong ngay do.")

    return "\n".join(lines)
