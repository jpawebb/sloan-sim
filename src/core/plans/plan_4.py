"""SLC Plan 4 implementation."""

from decimal import Decimal

from core.plans.base import LoanPlan, Frequency

# TODO: Load all figures from config.toml


class Plan4(LoanPlan):
    """SLC Plan 4 implementation. Earnings threshold has changed from £32,745 in 2025/26 to £33,795 in 2026/27."""

    loan_id = "plan_4"
    # TODO: replace with values from config.toml
    default_earning_threshold = 33_795
    default_payment_term = 30
    repayment_rate = 0.09

    def effective_interest_rate(self, user) -> Decimal:
        """Effective rate is the lower of RPI and the Bank of England (BOE) base rate + 1%."""
        return min(RPI, BOE_BASE_RATE + 0.01)
