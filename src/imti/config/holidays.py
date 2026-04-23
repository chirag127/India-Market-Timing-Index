"""Indian market holiday calendar for NSE/BSE.

Updated annually. Holidays determine whether the system runs in
market-hours mode or holiday/after-hours mode.
"""

from datetime import date

# NSE/BSE trading holidays for 2025
# Source: https://www.nseindia.com/resources/exchange-communication
NSE_HOLIDAYS_2025: set[date] = {
    # Republic Day
    date(2025, 1, 26),
    # Holi
    date(2025, 3, 14),
    # Id-Ul-Fitr (Eid)
    date(2025, 3, 31),
    # Shree Ram Navami
    date(2025, 4, 6),
    # Mahavir Jayanti
    date(2025, 4, 10),
    # Dr. Baba Saheb Ambedkar Jayanti
    date(2025, 4, 14),
    # Good Friday
    date(2025, 4, 18),
    # Maharashtra Day
    date(2025, 5, 1),
    # Muharram
    date(2025, 6, 7),
    # Mahatma Gandhi Jayanti
    date(2025, 10, 2),
    # Dussehra
    date(2025, 10, 20),
    # Diwali (Laxmi Pujan) — note: Muhurat Trading session in evening
    date(2025, 10, 21),
    # Diwali Balipratipada
    date(2025, 10, 22),
    # Prakash Gurpurab of Guru Nanak Dev
    date(2025, 11, 5),
    # Christmas
    date(2025, 12, 25),
}

# Half-day sessions (Muhurat Trading on Diwali evening)
NSE_HALF_DAYS_2025: set[date] = {
    date(2025, 10, 21),  # Diwali Laxmi Pujan — Muhurat Trading ~6:00–7:15 PM
}

# Combine all known holidays (add future years here)
ALL_HOLIDAYS: set[date] = NSE_HOLIDAYS_2025.copy()
ALL_HALF_DAYS: set[date] = NSE_HALF_DAYS_2025.copy()


def is_market_holiday(d: date) -> bool:
    """Check if a date is a market holiday."""
    # Weekends are always closed but not classified as "holidays"
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return d in ALL_HOLIDAYS


def is_half_day(d: date) -> bool:
    """Check if a date is a half-day session."""
    return d in ALL_HALF_DAYS


def is_weekend(d: date) -> bool:
    """Check if a date is a weekend."""
    return d.weekday() >= 5


def is_trading_day(d: date) -> bool:
    """Check if a date is a regular trading day."""
    return not is_weekend(d) and not is_market_holiday(d)
