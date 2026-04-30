"""Singleton loader for resources/config.toml with date-aware value resolution."""

from __future__ import annotations

from pathlib import Path
import sys
from datetime import date
from decimal import Decimal

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_CONFIG_PATH = Path(__file__).parent.parent.parent / "resources" / "config.toml"


def _resolve_as_of(series: list[dict], as_of: date) -> dict:
    """Return the entry from a time-series list whose date is the latest on or before `as_of`.

    Args:
        series: List of dicts, each containing a ``date`` key and one or more value keys.
        as_of: The reference date; the most recent entry on or before this date is returned.

    Raises:
        ValueError: If no entry exists on or before `as_of`.

    """
    eligible = [entry for entry in series if entry["date"] <= as_of]
    if not eligible:
        raise ValueError(
            f"No entry found on or before {as_of}. "
            f"Earliest available date is {min(e['date'] for e in series)}"
        )
    return max(eligible, key=lambda e: e["date"])


class ConfigLoader:
    """Singleton accessor for ``resources/config.toml``.

    Reads the TOML file once on instantiation, and caches it.
    All accessors accept an optional as_of date; when omitted
    ``date.today()`` is used. -> time-aware resolution.

    Example:
        >>> cfg = ConfigLoader()
        >>> cfg.rpi()
        0.032
        >>> cfg.earnings_threshold("plan_2")
        29385

    """

    _instance: ConfigLoader | None = None
    _data: dict

    def __new__(cls) -> ConfigLoader:
        """Initialist the class.

        Returns:
            ConfigLoader: The singleton instance of the class.

        """
        if cls._instance is None:
            instance = super().__new__(cls)
            with open(_CONFIG_PATH, "rb") as f:
                instance._data = tomllib.load(f)
            cls._instance = instance
        return cls._instance

    # MACROECONOMIC HELPERS
    def rpi(self, as_of: date | None = None) -> Decimal:
        """Retail Price Index (RPI) applicable on the given date."""
        return Decimal(
            _resolve_as_of(self._data["economics"]["rpi"], as_of or date.today())[
                "value"
            ]
        )

    def boe_base_rate(self, as_of: date | None = None) -> Decimal:
        """Bank of England base rate applicable on the given date."""
        return Decimal(
            _resolve_as_of(
                self._data["economics"]["boe_base_rate"], as_of or date.today()
            )["value"]
        )

    def prevailing_market_rate_cap(self, as_of: date | None = None) -> Decimal:
        """Prevailing Market Rate (PMR) cap applicable on the given date."""
        return Decimal(
            _resolve_as_of(
                self._data["economics"]["prevailing_market_rate_cap"],
                as_of or date.today(),
            )["value"]
        )

    # PER-PLAN HELPERS
    def earnings_threshold(self, plan: str, as_of: date | None = None) -> Decimal:
        """Repayment earnings threshold for ``plan_id`` applicable on the given date."""
        series = self._data["plans"][plan]["earnings_threshold"]
        return Decimal(_resolve_as_of(series, as_of or date.today())["value"])

    def interest_thresholds(
        self, plan: str, as_of: date | None = None
    ) -> (Decimal, Decimal):
        """Return ``(lower, upper)`` interest band thresholds for ``plan_id`` applicable on given date."""
        series = self._data["plans"][plan]["interest_thresholds"]
        entry = _resolve_as_of(series, as_of or date.today())
        return Decimal(entry["lower_value"]), Decimal(entry["upper_value"])

    def vir_margin(self, plan: str, as_of: date | None = None) -> Decimal:
        """Variable Interest Rate (VIR) margin for ``plan_id`` applicable on the given date."""
        return Decimal(self._data["plans"][plan]["vir_margin"])

    def repayment_rate(self, plan: str) -> Decimal:
        """Repayment rate for ``plan_id``."""
        return Decimal(self._data["plans"][plan]["repayment_rate"])

    def repayment_period(self, plan: str) -> Decimal:
        """Repayment period for ``plan_id``."""
        return Decimal(self._data["plans"][plan]["repayment_period"])
