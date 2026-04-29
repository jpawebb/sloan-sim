"""SLC Plan 1 implementation."""

from decimal import Decimal

from core.config import ConfigLoader
from core.plans.base import LoanPlan

_cfg = ConfigLoader()


class Plan1(LoanPlan):
    """SLC Plan 1 implementation. Earnings threshold has changed from £26,065 in 2025/26 to £26,900 in 2026/27."""

    loan_id = "plan_1"
    earnings_threshold = _cfg.earnings_threshold(loan_id)
    repayment_rate = _cfg.repayment_rate(loan_id)
    repayment_period = _cfg.repayment_period(loan_id)

    def effective_interest_rate(self, user) -> Decimal:
        """Effective rate is the lower of RPI and the Bank of England (BOE) base rate + 1%."""
        return min(_cfg.rpi(), _cfg.boe_base_rate() + Decimal(0.01))
