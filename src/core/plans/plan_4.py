"""SLC Plan 4 implementation."""

from decimal import Decimal

from core.plans.base import LoanPlan, Frequency
from core.loan_engine import RPI, BOE_BASE_RATE  # TODO: move this to a rates.yml


class Plan4(LoanPlan):
    """SLC Plan 4 implementation. Earnings threshold has changed from £32,745 in 2025/26 to £33,795 in 2026/27."""

    loan_id = "plan_4"
    default_earning_threshold = 33_795
    default_payment_term = 30
    repayment_rate = 0.09

    def effective_interest_rate(self, user) -> Decimal:
        """Effective rate is the lower of RPI and the Bank of England (BOE) base rate + 1%."""
        return min(RPI, BOE_BASE_RATE + 0.01)
