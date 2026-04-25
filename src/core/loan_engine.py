"""Core loan engine for calculating effective interest rates and repayment schedules for Student Loan Company (SLC) loans."""

from __future__ import annotations
from enum import Enum
from typing import List

# Applicable retail price index (RPI) from September 1st, 2025 to 31 August 2026
RPI = 0.032

# Bank rate of the Bank of England (BOE), is used as a boundry for interest rates for plan 1 and plan 4 loans
BOE_BASE_RATE = 0.0375

# Variable interest rate (VIR) margin is the maximum premium above RPI that can be applied to the loan balance for plan 2.
# Total cap for plan 2 (RPI + VIR) will be 6% starting September 1st, 2026.
PLAN_2_VIR = 0.03

# Preemptive incoming cap of 6% September 1st, 2026 for plans 2, 3, and 5
PREVAILING_MARKET_RATE_CAP = 0.06
EMERGENCY_POLICY_CAP = 0.06

# Interest rate specific thresholds
PLAN_TWO_LOWER_INTEREST_THRESHOLD = 29385
PLAN_TWO_UPPER_INTEREST_THRESHOLD = 52885


class LoanProduct:
    """The structured loan product offered by Student Loan Company (SLC).

    Args:
        loan_id (str): Internal name for the loan product, e.g. "plan_2"
        earning_threshold (float): Debtors earning threshold, above which payment is required, e.g. 27295 for plan_2
        payment_term_years (int): Lifetime of the loan, after which it is forgiven, e.g. 30 for plan_2
        interest_application_window (InterestApplicationWindow): How often is the annualised interest rate applied to the loan balance, e.g. "daily"

    """

    def __init__(
        self,
        loan_id: str,
        earning_threshold: float,
        payment_term_years: int,
        interest_application_window: InterestApplicationWindow,
    ):
        """Represent a structured loan product offered by Student Loan Company (SLC)."""
        self.loan_id = loan_id
        self.earning_threshold = earning_threshold
        self.payment_term_years = payment_term_years
        self.interest_application_window = interest_application_window


class UsersLoanProduct(LoanProduct):
    """The user's specific loan product, with additional attributes to calculate the effective interest rate and repayment schedule.

    Args:
        user (User): The user associated with this loan product, e.g. "user_1"
        loan_id (str): Internal name for the loan product, e.g. "plan_2"
        earning_threshold (float): Debtors earning threshold, above which payment is required, e.g. 27295 for plan_2
        payment_term_years (int): Lifetime of the loan, after which it is forgiven, e.g. 30 for plan_2
        interest_application_window (InterestApplicationWindow): How often is the annualised interest rate applied to the loan balance, e.g. "daily"
        balance (float): The user's current outstanding loan balance, e.g. 45000
        years_since_graduation (int): The number of years since the user graduated. This can be used to determine how long the user has been repaying their loan, and how many years they have left until their loan is forgiven, e.g. 5

    """

    def __init__(
        self,
        user: User,
        loan_id: str,
        earning_threshold: float,
        payment_term_years: int,
        interest_application_window: InterestApplicationWindow,
        balance: float,
        years_since_graduation: int,
    ):
        """Inherits from LoanProduct, but with additional user-specific attributes, e.g. loan balance and years since graduation."""
        super().__init__(
            loan_id,
            earning_threshold,
            payment_term_years,
            interest_application_window,
        )
        self.user = user
        self.balance = balance
        self.years_since_graduation = years_since_graduation

    @property
    def effective_interest_rate(self) -> Decimal:
        """Calculate the effective interest rate for this user's loan product."""
        from core.plans import get_plan

        return get_plan(self.loan_id).effective_interest_rate(self.user)


class User:
    """The user of the SLC loan repayment calculator.

    Args:
        user_id (str): Internal name for the user, e.g. "user_1"
        annual_income (float): The user's annual income, e.g. 30000
        loans (List[UsersLoanProduct]): The user's loan products, e.g. personal plan_2 and postgraduate loans

    """

    def __init__(
        self,
        user_id: str,
        annual_income: float,
        loans: List[UsersLoanProduct] = None,
    ):
        """Represent the user of the SLC loan repayment calculator."""
        self.user_id = user_id
        self.annual_income = annual_income
        self.loans = loans if loans else []


if __name__ == "__main__":
    pass
