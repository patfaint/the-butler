"""Coffee price algorithm — calculates the dynamic coffee amount for a domme."""

from datetime import datetime, timezone
from typing import Optional


# ── Multiplier constants ───────────────────────────────────────────────────────

# Time-of-day multipliers (hour → multiplier)
_TIME_MULTIPLIERS: dict[tuple[int, int], float] = {
    (6, 9): 1.2,    # Early morning — freshly woken, maximum demand
    (9, 12): 1.1,   # Mid-morning
    (12, 17): 1.0,  # Afternoon — baseline
    (17, 21): 1.15, # Evening — prime time
    (21, 24): 1.25, # Late night — rare and therefore expensive
    (0, 6): 1.3,    # Overnight — extremely rare treat
}

# Day-of-week multipliers (weekday() → multiplier; 0 = Monday)
_DAY_MULTIPLIERS: dict[int, float] = {
    0: 1.0,   # Monday
    1: 1.0,   # Tuesday
    2: 1.0,   # Wednesday
    3: 1.05,  # Thursday — start of the weekend run-up
    4: 1.15,  # Friday
    5: 1.25,  # Saturday
    6: 1.2,   # Sunday
}

# Drought multipliers — number of drought days → multiplier
_DROUGHT_THRESHOLDS: list[tuple[int, float]] = [
    (0, 1.0),   # Same day / no drought
    (1, 1.05),  # 1 day since last coffee
    (3, 1.15),  # 3+ days
    (7, 1.30),  # A week
    (14, 1.50), # Two weeks — they've been very neglectful
]


def _time_multiplier(hour: int) -> float:
    for (start, end), mult in _TIME_MULTIPLIERS.items():
        if start <= hour < end:
            return mult
    return 1.0


def _day_multiplier(weekday: int) -> float:
    return _DAY_MULTIPLIERS.get(weekday, 1.0)


def _drought_multiplier(days_since_last_coffee: int) -> float:
    multiplier = 1.0
    for threshold, mult in _DROUGHT_THRESHOLDS:
        if days_since_last_coffee >= threshold:
            multiplier = mult
    return multiplier


def calculate_coffee_amount(
    base_amount: float,
    *,
    time_scaling: bool = False,
    day_scaling: bool = False,
    drought_scaling: bool = False,
    last_coffee_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> float:
    """Return the dynamic coffee amount for a domme's current request.

    Args:
        base_amount: The domme's configured base coffee amount (e.g. 10.0).
        time_scaling: Whether to apply a time-of-day multiplier.
        day_scaling: Whether to apply a day-of-week multiplier.
        drought_scaling: Whether to apply a drought (days since last coffee) multiplier.
        last_coffee_at: UTC datetime of the last coffee request (for drought calc).
        now: Override "current time" — useful for testing.

    Returns:
        Calculated coffee amount, rounded to 2 decimal places.
    """
    if now is None:
        now = datetime.now(tz=timezone.utc)

    multiplier = 1.0

    if time_scaling:
        multiplier *= _time_multiplier(now.hour)

    if day_scaling:
        multiplier *= _day_multiplier(now.weekday())

    if drought_scaling:
        if last_coffee_at is not None:
            days_since = (now - last_coffee_at).days
        else:
            days_since = 14  # No record → maximum drought multiplier
        multiplier *= _drought_multiplier(days_since)

    return round(base_amount * multiplier, 2)
