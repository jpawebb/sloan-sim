"""SLC Plan 3 implementation."""

from decimal import Decimal

from core.plans.base import LoanPlan, Frequency

# TODO: Load all figures from config.toml


class Plan3(LoanPlan):
    """SLC Plan 3 implementation. Earnings threshold has remained at £21,000 in 2025/26 to 2026/27."""

    loan_id = "plan_3"
    aliases = ("postgraduate",)
    # TODO: replace with values from config.toml
    default_earning_threshold = 21_000
    default_payment_term = 30
    repayment_rate = 0.06

    def effective_interest_rate(self, user) -> Decimal:
        """Effective rate is the lower of RPI and the Bank of England (BOE) base rate + 1%."""
        return min(RPI + 0.03, min(PREVAILING_MARKET_RATE_CAP, EMERGENCY_POLICY_CAP))
