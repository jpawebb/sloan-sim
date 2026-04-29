"""Definitions for Student Loan Company (SLC) loan plans and interest logic."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from decimal import Decimal
from enum import Enum

if TYPE_CHECKING:
    from core.loan_engine import User


class Frequency(Enum):
    """Different frequencies for interest calculation and application windows."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUALLY = "annually"


class LoanPlan(ABC):
    r"""Abstract base class for Student Loan Company (SLC) repayment plans.

    The daily interest rate $r$ is calculated as the nominal simple interest rate:
    $$r = \frac{\text{annual\_rate}}{365}$$
    Interest accumulates daily and is added to the principal balance at the end
    of each month, resulting in monthly compounding.

    The effective interest rate is the annualised rate that accounts for this
    compounding effect.

    Attributes:
        loan_id: Unique identifier for the loan plan.
        aliases: Alternative names for the plan.
        earnings_threshold: Minimum income before repayments start.
        repayment_period: Duration of the loan before write-off.
        repayment_rate: Percentage of income over the threshold taken for payment.

    Example:
        Initial balance: £30,000 at 6% annual interest.
        Daily interest: $30,000 \times (0.06 / 365) \approx £4.93$
        Month 1 (30 days): $£4.93 \times 30 = £147.95$
        Month 1 end balance: $£30,147.95$
        Month 2 (30 days): $30,147.95 \times (0.06 / 365) \times 30 \approx £148.67$

    """

    loan_id: str
    aliases: tuple[str, ...] = ()
    earnings_threshold: (
        Decimal  # TODO: these need to stored in a rates.yml or similar, not hardcoded
    )
    repayment_period: int
    default_interest_calculation_window: Frequency = Frequency.DAILY
    default_interest_application_window: Frequency = Frequency.MONTHLY
    repayment_rate: Decimal

    @abstractmethod
    def effective_interest_rate(self, user: User) -> Decimal:
        """Return the annualised effective rate for this borrower, today."""
