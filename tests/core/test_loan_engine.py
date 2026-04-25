"""Unit tests for the core loan engine logic, including interest calculations and user-loan interactions."""

from core.loan_engine import (
    User,
    UsersLoanProduct,
    PLAN_TWO_LOWER_INTEREST_THRESHOLD,
    RPI,
    BOE_BASE_RATE,
    PREVAILING_MARKET_RATE_CAP,
    PLAN_2_VIR,
    PLAN_TWO_UPPER_INTEREST_THRESHOLD,
)
from core.plans.base import Frequency
import pytest


# Helper fixture to create a default loan setup
@pytest.fixture
def base_loan_args():
    """Represent a base test loan."""
    return {
        "loan_id": "plan_2",
        "earning_threshold": 27295,
        "payment_term_years": 30,
        "interest_application_window": Frequency.DAILY,
        "balance": 45000,
        "years_since_graduation": 2,
    }


def test_user_loan_linking():
    """Test the link between User and their Loans."""
    user = User("user_1", 30000)
    loan = UsersLoanProduct(
        user=user,
        **{
            "loan_id": "plan_2",
            "earning_threshold": 29385,
            "payment_term_years": 30,
            "interest_application_window": Frequency.DAILY,
            "balance": 10000,
            "years_since_graduation": 2,
        },
    )
    user.loans.append(loan)

    assert loan.user.annual_income == 30000
    assert len(user.loans) == 1
    assert user.loans[0].balance == 10000


@pytest.mark.parametrize(
    "income, expected_rate",
    [
        # Below lower threshold: RPI only
        (PLAN_TWO_LOWER_INTEREST_THRESHOLD - 5000, RPI),
        # At lower boundary: RPI only
        (PLAN_TWO_LOWER_INTEREST_THRESHOLD, RPI),
        # At upper boundary: RPI + VIR
        (
            PLAN_TWO_UPPER_INTEREST_THRESHOLD,
            min(RPI + PLAN_2_VIR, PREVAILING_MARKET_RATE_CAP),
        ),
        # Above upper boundary: Capped at ceiling (RPI + VIR, but capped by prevailing market rate cap)
        (
            PLAN_TWO_UPPER_INTEREST_THRESHOLD + 5000,
            min(RPI + PLAN_2_VIR, PREVAILING_MARKET_RATE_CAP),
        ),
        # Midpoint (RPI + half of VIR)
        (
            (PLAN_TWO_LOWER_INTEREST_THRESHOLD + PLAN_TWO_UPPER_INTEREST_THRESHOLD) / 2,
            RPI + (PLAN_2_VIR / 2),
        ),
    ],
)
def test_plan_2_interest_logic(income, expected_rate, base_loan_args):
    """Test the interest logic for Plan 2 loans across different income levels."""
    user = User("test_user", income)
    loan = UsersLoanProduct(user=user, **base_loan_args)

    assert loan.effective_interest_rate == pytest.approx(expected_rate)


def test_plan_3_interest_logic(base_loan_args):
    """Test the interest logic for Plan 3 loans."""
    user = User("high_earner", 100_000)
    base_loan_args["loan_id"] = "plan_3"
    loan = UsersLoanProduct(user=user, **base_loan_args)

    assert loan.effective_interest_rate == pytest.approx(
        min(RPI + 0.03, PREVAILING_MARKET_RATE_CAP)
    )


def test_plan_1_interest_logic(base_loan_args):
    """Test the interest logic for Plan 1 loans."""
    user = User("any_income", 25000)
    base_loan_args["loan_id"] = "plan_1"
    loan = UsersLoanProduct(user=user, **base_loan_args)

    assert loan.effective_interest_rate == pytest.approx(min(RPI, BOE_BASE_RATE + 0.01))
