"""SLC Plan 3 implementation."""

from decimal import Decimal

from core.config import ConfigLoader
from core.plans.base import LoanPlan, Frequency

_cfg = ConfigLoader()


class Plan3(LoanPlan):
    """SLC Plan 3 implementation. Earnings threshold has remained at £21,000 in 2025/26 to 2026/27."""

    loan_id = "plan_3"
    aliases = ("postgraduate",)
    earnings_threshold = _cfg.earnings_threshold(loan_id)
    repayment_rate = _cfg.repayment_rate(loan_id)
    repayment_period = _cfg.repayment_period(loan_id)

    def effective_interest_rate(self, user) -> Decimal:
        """Effective rate is the RPI + 3%, capped at the prevailing market rate cap."""
        return min(_cfg.rpi() + Decimal(0.03), _cfg.prevailing_market_rate_cap())
