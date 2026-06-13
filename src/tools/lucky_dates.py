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
    birth_date: str,
    from_date: str | None = None,
    days: int = 14,
) -> str:
    """
    Tinh ngay gio tot cho user dua tren ngay sinh.

    Args:
        birth_date: Ngay sinh YYYY-MM-DD hoac YYYY
        from_date:  Bat dau xem tu ngay nao (YYYY-MM-DD), mac dinh hom nay
        days:       So ngay xem phia truoc (mac dinh 14)

    Returns:
        Formatted string cho Telegram.
    """
    # Parse birth_date
    try:
        if len(birth_date) == 4:
            birth_year = int(birth_date)
        else:
            birth_year = date.fromisoformat(birth_date).year
    except Exception:
        return "Khong doc duoc ngay sinh. Vui long nhap dinh dang YYYY-MM-DD hoac YYYY."

    chi_tuoi = _chi_of_birth_year(birth_year)
    animal_tuoi = CHI_ANIMAL[chi_tuoi]

    start = date.fromisoformat(from_date) if from_date else date.today()
    results: list[DayInfo] = []

    for i in range(days):
        d = start + timedelta(days=i)
        can, chi = _can_chi_of_date(d)
        score = _day_score(can, chi, chi_tuoi)
        rel = _relation(chi_tuoi, chi)
        lucky_hrs = _lucky_hours(chi)
        wd = _WEEKDAY_VN[d.weekday()]
        note = _build_note(can, chi, rel, score)
        results.append(DayInfo(
            date_str=d.isoformat(),
            weekday=wd,
            can=can, chi=chi,
            score=score,
            relation=rel,
            lucky_hours=lucky_hrs,
            note=note,
        ))

    return _format_output(results, chi_tuoi, animal_tuoi, birth_year)


def _build_note(can: str, chi: str, rel: str, score: int) -> str:
    rel_text = {
        "tam_hop": "Tam Hop - rat tot",
        "hop": "Luc Hop - tot",
        "hoa": "Cung chi - binh thuong",
        "binh": "Binh thuong",
        "xung": "Luc Xung - tranh di chuyen neu co the",
    }
    base = rel_text.get(rel, "")
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
    if base:
        return f"{prefix}, {base.lower()}"
    return prefix


def _level_emoji(score: int) -> str:
    """Emoji muc do thay cho thanh diem so."""
    if score >= 80:
        return "🟢"  # rat tot
    if score >= 65:
        return "🟢"  # tot
    if score >= 50:
        return "🟡"  # binh thuong
    if score >= 35:
        return "🟠"  # nen can nhac
    return "🔴"       # tranh


def _level_word(score: int) -> str:
    if score >= 80:
        return "rat tot"
    if score >= 65:
        return "tot"
    if score >= 50:
        return "binh thuong"
    if score >= 35:
        return "nen can nhac"
    return "nen tranh"


def _format_output(days: list[DayInfo], chi_tuoi: str, animal: str, birth_year: int) -> str:
    good_days = [d for d in days if d.score >= 65]
    start_str = days[0].date_str
    end_str = days[-1].date_str

    lines = []
    lines.append(f"Tuoi {chi_tuoi} {animal} ({birth_year}), minh xem ngay xuat hanh tu {start_str} den {end_str} cho ban.")
    lines.append("")

    if good_days:
        top = sorted(good_days, key=lambda x: x.score, reverse=True)
        best = top[0]
        gio = ", ".join(f"{g['time']} ({g['chi']} {g['animal']})" for g in best.lucky_hours[:3])
        lines.append(f"Ngay dep nhat la {best.date_str} ({best.weekday}), ngay {best.can} {best.chi} {CHI_ANIMAL[best.chi]} - {best.note.lower()}.")
        lines.append(f"Gio tot trong ngay do: {gio}.")
        lines.append("")

        if len(top) > 1:
            lines.append("May ngay khac cung dep neu ban can lui lich:")
            for d in top[1:4]:
                lines.append(f"{_level_emoji(d.score)} {d.date_str} ({d.weekday}) - ngay {d.chi} {CHI_ANIMAL[d.chi]}, {_level_word(d.score)}")
            lines.append("")
    else:
        lines.append("Trong khoang nay khong co ngay that su dep, nhung van co the di duoc.")
        lines.append("")

    # Cac ngay nen tranh (score thap)
    bad_days = [d for d in days if d.score < 50]
    if bad_days:
        bad_str = ", ".join(f"{d.date_str} ({d.weekday})" for d in bad_days[:4])
        lines.append(f"Nen tranh hoac can than: {bad_str}.")
        lines.append("")

    lines.append("Ban muon minh tim ve may bay cho ngay nao trong so nay khong?")

    return "\n".join(lines)
