"""Unit tests for the core loan engine logic, including interest calculations and user-loan interactions."""

from decimal import Decimal
import pytest

from core.config import ConfigLoader
from core.loan_engine import User, UsersLoanProduct
from core.plans.base import Frequency

_cfg = ConfigLoader()

_RPI = _cfg.rpi()
_BOE = _cfg.boe_base_rate()
_PMR_CAP = _cfg.prevailing_market_rate_cap()
_VIR = _cfg.vir_margin("plan_2")
_P2_LO, _P2_HI = _cfg.interest_thresholds("plan_2")


# Helper fixture to create a default loan setup
@pytest.fixture
def base_loan_args():
    """Represent a base test loan."""
    return {
        "loan_id": "plan_2",
        "earnings_threshold": _cfg.earnings_threshold("plan_2"),
        "repayment_period": _cfg.repayment_period("plan_2"),
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
            "earnings_threshold": _cfg.earnings_threshold("plan_2"),
            "repayment_period": _cfg.repayment_period("plan_2"),
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
        (_P2_LO - 5000, _RPI),
        # At lower boundary: RPI only
        (_P2_LO, _RPI),
        # At upper boundary: RPI + VIR (capped)
        (_P2_HI, min(_RPI + _VIR, _PMR_CAP)),
        # Above upper boundary: Capped at ceiling (RPI + VIR, but capped by prevailing market rate cap)
        (_P2_HI + 5000, min(_RPI + _VIR, _PMR_CAP)),
        # Midpoint (RPI + half of VIR)
        ((_P2_LO + _P2_HI) / 2, _RPI + (_VIR / 2)),
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
        min(_RPI + Decimal(0.03), _PMR_CAP)
    )


def test_plan_1_interest_logic(base_loan_args):
    """Test the interest logic for Plan 1 loans."""
    user = User("any_income", 25000)
    base_loan_args["loan_id"] = "plan_1"
    loan = UsersLoanProduct(user=user, **base_loan_args)

    assert loan.effective_interest_rate == pytest.approx(
        min(_RPI, _BOE + Decimal(0.01))
    )
