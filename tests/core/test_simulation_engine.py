"""Tests for the monthly simulation engine."""

from datetime import date
from decimal import Decimal

import pytest

from core.config import ConfigLoader
from core.simulation_engine import simulate
from core.loan_engine import User, UsersLoanProduct
from core.plans.base import Frequency

_cfg = ConfigLoader()


@pytest.fixture
def plan_2_user():
    """User with one Plan 2 loan, £30,000 balance, 2 years since graduation, and an annual income of £35,000."""
    user = User("test", annual_income=35_000)
    loan = UsersLoanProduct(
        user=user,
        loan_id="plan_2",
        earnings_threshold=_cfg.earnings_threshold("plan_2"),
        repayment_period=int(_cfg.repayment_period("plan_2")),
        interest_application_window=Frequency.MONTHLY,
        balance=30_000,
        years_since_graduation=2,
    )
    user.loans.append(loan)
    return user


def test_simulate_returns_result(plan_2_user):
    """Simulate produces a non-empty result set SimulationResult object."""
    result = simulate(
        plan_2_user, start_date=date(2026, 4, 1), salary_growth=Decimal("0.03")
    )
    assert "plan_2" in result.loans
    assert len(result.loans["plan_2"].ledger) > 0
