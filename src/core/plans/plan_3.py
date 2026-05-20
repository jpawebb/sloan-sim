"""SLC Plan 3 implementation."""

from decimal import Decimal
from datetime import date

from src.core.config import ConfigLoader
from .base import LoanPlan

_cfg = ConfigLoader()


class Plan3(LoanPlan):
    """SLC Plan 3 implementation. Earnings threshold has remained at £21,000 in 2025/26 to 2026/27."""

    loan_id = "plan_3"
    aliases = ("postgraduate",)

    def effective_interest_rate(self, user, as_of: date = None) -> Decimal:
        """Effective rate is the RPI + 3%, capped at the prevailing market rate cap."""
        if as_of == None:
            as_of = date.today()

        rpi = _cfg.rpi(as_of=as_of)
        cap = _cfg.prevailing_market_rate_cap(as_of=as_of)

        return min(rpi + Decimal(0.03), cap)
