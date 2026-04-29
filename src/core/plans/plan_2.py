"""SLC Plan 2 implementation."""

from decimal import Decimal

from core.config import ConfigLoader
from core.plans.base import LoanPlan

_cfg = ConfigLoader()


class Plan2(LoanPlan):
    """SLC Plan 2 implementation. Earnings threshold has changed from £28,470 in 2025/26 to £29,385 in 2026/27."""

    loan_id = "plan_2"
    earnings_threshold = _cfg.earnings_threshold(loan_id)
    repayment_rate = _cfg.repayment_rate(loan_id)
    repayment_period = _cfg.repayment_period(loan_id)

    def effective_interest_rate(self, user) -> Decimal:
        """Sliding scale between RPI and RPI + VIR margin, capped by prevailing market rate cap.

        - At or below lower threshold: RPI only.
        - At or above upper threshold: RPI + VIR.
        - Between the two: linear interpolation.
        - Always capped at the prevailing market rate cap.
        """
        rpi = _cfg.rpi()
        vir = _cfg.vir_margin(self.loan_id)
        cap = _cfg.prevailing_market_rate_cap()
        lo, hi = _cfg.interest_thresholds(self.loan_id)

        if user.annual_income <= lo:
            rate = rpi
        elif user.annual_income >= hi:
            rate = rpi + vir
        else:
            ratio = (user.annual_income - lo) / (hi - lo)
            rate = rpi + (ratio * vir)
        return min(rate, cap)
