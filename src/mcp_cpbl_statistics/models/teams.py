# CPBL team codes — rarely change (only on team disbandment or rename)
# Last verified: 2026 season

TEAM_CODES: dict[str, str] = {
    "ACN011": "中信兄弟",
    "AAA011": "味全龍",
    "ADD011": "統一7-ELEVEn獅",
    "AEO011": "富邦悍將",
    "AJL011": "樂天桃猿",
    "AKP011": "台鋼雄鷹",
    # historical
    "AJK011": "Lamigo",
}

# reverse map: name → code (partial match friendly)
_NAME_TO_CODE: dict[str, str] = {v: k for k, v in TEAM_CODES.items()}


def resolve_team_code(name_or_code: str) -> str | None:
    """Resolve a team name or code to a team code.

    Accepts exact code, exact name, or partial name match.
    Returns None if not found.
    """
    s = name_or_code.strip()
    if not s:
        return None
    # exact code
    if s in TEAM_CODES:
        return s
    # exact name
    if s in _NAME_TO_CODE:
        return _NAME_TO_CODE[s]
    # partial name match
    for name, code in _NAME_TO_CODE.items():
        if s in name:
            return code
    return None
