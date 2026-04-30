"""SLC Plan 5 implementation."""

from decimal import Decimal

from core.config import ConfigLoader
from core.plans.base import LoanPlan

_cfg = ConfigLoader()


class Plan5(LoanPlan):
    """SLC Plan 5 implementation. Earnings threshold has remained at £25,000 from 2025/26 to 2026/27."""

    loan_id = "plan_5"
    earnings_threshold = _cfg.earnings_threshold(loan_id)
    repayment_rate = _cfg.repayment_rate(loan_id)
    repayment_period = _cfg.repayment_period(loan_id)

    def effective_interest_rate(self, user) -> Decimal:
        """Effective rate is the RPI, capped at the prevailing market rate (PMR) cap."""
        return min(_cfg.rpi(), _cfg.prevailing_market_rate_cap())
