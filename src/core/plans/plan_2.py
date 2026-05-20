"""SLC Plan 2 implementation."""

from decimal import Decimal
from datetime import date

from src.core.config import ConfigLoader
from .base import LoanPlan

_cfg = ConfigLoader()


class Plan2(LoanPlan):
    """SLC Plan 2 implementation. Earnings threshold has changed from £28,470 in 2025/26 to £29,385 in 2026/27."""

    loan_id = "plan_2"

    def effective_interest_rate(self, user, as_of: date = None) -> Decimal:
        """Sliding scale between RPI and RPI + VIR margin, capped by prevailing market rate cap.

        - At or below lower threshold: RPI only.
        - At or above upper threshold: RPI + VIR.
        - Between the two: linear interpolation.
        - Always capped at the prevailing market rate cap.
        """
        if as_of == None:
            as_of = date.today()

        # Dynamic chronological lookups from config.toml
        rpi = _cfg.rpi(as_of=as_of)
        vir = _cfg.vir_margin(self.loan_id, as_of=as_of)
        cap = _cfg.prevailing_market_rate_cap(as_of=as_of)
        lo, hi = _cfg.interest_thresholds(self.loan_id, as_of=as_of)

        # Evaluate based on current simulation-loop income state
        income = user.annual_income

        if income <= lo:
            rate = rpi
        elif income >= hi:
            rate = rpi + vir
        else:
            ratio = (income - lo) / (hi - lo)
            rate = rpi + (ratio * vir)

        return min(rate, cap)
