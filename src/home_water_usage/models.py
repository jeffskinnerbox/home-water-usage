"""Core data model dataclasses."""
from dataclasses import dataclass
from datetime import date


@dataclass
class UsageRecord:
    date: date
    gallons: int


@dataclass
class SeasonalAverage:
    season: str
    avg_gallons: float
