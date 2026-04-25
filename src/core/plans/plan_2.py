"""SLC Plan 2 implementation."""

from decimal import Decimal

from core.plans.base import LoanPlan, Frequency
from core.loan_engine import (
    RPI,
    BOE_BASE_RATE,
    PLAN_2_VIR,
    PLAN_TWO_LOWER_INTEREST_THRESHOLD,
    PLAN_TWO_UPPER_INTEREST_THRESHOLD,
    PREVAILING_MARKET_RATE_CAP,
    EMERGENCY_POLICY_CAP,
)  # TODO: move this to a rates.yml


class Plan2(LoanPlan):
    """SLC Plan 2 implementation. Earnings threshold has changed from £28,470 in 2025/26 to £29,385 in 2026/27."""

    loan_id = "plan_2"
    default_earning_threshold = 29_385
    default_payment_term = 30
    repayment_rate = 0.09

    def effective_interest_rate(self, user) -> Decimal:
        """Sliding scale.

        Effective rate is calculated based on the borrower's income, with a sliding scale between
        RPI and RPI + VIR, capped at the prevailing market rate cap and emergency policy cap.
        """
        ceiling = min(PREVAILING_MARKET_RATE_CAP, EMERGENCY_POLICY_CAP)
        lo, hi = PLAN_TWO_LOWER_INTEREST_THRESHOLD, PLAN_TWO_UPPER_INTEREST_THRESHOLD

        if user.annual_income <= lo:
            rate = RPI
        elif user.annual_income >= hi:
            rate = RPI + PLAN_2_VIR
        else:
            ratio = (user.annual_income - lo) / (hi - lo)
            rate = RPI + (ratio * PLAN_2_VIR)
        return min(rate, ceiling)
