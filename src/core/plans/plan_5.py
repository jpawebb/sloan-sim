"""SLC Plan 5 implementation."""

from decimal import Decimal
from datetime import date

from src.core.config import ConfigLoader
from .base import LoanPlan

_cfg = ConfigLoader()


class Plan5(LoanPlan):
    """SLC Plan 5 implementation. Earnings threshold has remained at £25,000 from 2025/26 to 2026/27."""

    loan_id = "plan_5"

    def effective_interest_rate(self, user, as_of: date = None) -> Decimal:
        """Effective rate is the RPI, capped at the prevailing market rate (PMR) cap."""
        if as_of is None:
            as_of = date.today()

        rpi = _cfg.rpi(as_of=as_of)
        cap = _cfg.prevailing_market_rate_cap(as_of=as_of)

        return min(rpi, cap)
