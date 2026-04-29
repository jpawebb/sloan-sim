"""SLC Plan 5 implementation."""

from decimal import Decimal

from core.plans.base import LoanPlan, Frequency

# TODO: Load all figures from config.toml


class Plan5(LoanPlan):
    """SLC Plan 5 implementation. Earnings threshold has remained at £25,000 from 2025/26 to 2026/27."""

    loan_id = "plan_5"
    # TODO: replace with values from config.toml
    default_earning_threshold = 25_000
    default_payment_term = 40
    repayment_rate = 0.09

    def effective_interest_rate(self, user) -> Decimal:
        """Effective rate is the lower of RPI and the Bank of England (BOE) base rate + 1%."""
        return min(RPI, BOE_BASE_RATE + 0.01)
