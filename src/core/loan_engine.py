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


class InterestApplicationWindow(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUALLY = "annually"


class LoanProduct:
    def __init__(
        self,
        loan_id: str,
        earning_threshold: float,
        payment_term_years: int,
        interest_application_window: InterestApplicationWindow,
    ):
        """The structured loan product offered by Student Loan Company (SLC).

        Args:
            loan_id (str): Internal name for the loan product, e.g. "plan_2"
            earning_threshold (float): Debtors earning threshold, above which payment is required, e.g. 27295 for plan_2
            payment_term_years (int): Lifetime of the loan, after which it is forgiven, e.g. 30 for plan_2
            interest_application_window (InterestApplicationWindow): How often is the annualised interest rate applied to the loan balance, e.g. "daily"
        """
        self.loan_id = loan_id
        self.earning_threshold = earning_threshold
        self.payment_term_years = payment_term_years
        self.interest_application_window = interest_application_window


class UsersLoanProduct(LoanProduct):
    # Inherits from LoanProduct, but with additional user-specific attributes, e.g. loan balance and years since graduation
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
    def effective_interest_rate(self) -> float:
        """The effective interest rate applied to the user's loan balance, which can be different from the nominal interest rate defined in the loan product, due to various caps and adjustments based on the user's income and loan type."""

        effective_ceiling = min(PREVAILING_MARKET_RATE_CAP, EMERGENCY_POLICY_CAP)

        if self.loan_id == "plan_1" or self.loan_id == "plan_4":
            # For plan 1 and plan 4 loans, the effective interest rate is the lower of RPI and the Bank of England (BOE) rate + 1%
            return min(RPI, BOE_BASE_RATE + 0.01)

        if self.loan_id == "plan_2":
            # Not to be confused with salary thresholds for repayment, which are different and defined in LoanProduct.earning_threshold
            # This is for determining the effective interest rate applied to the loan balance, which is capped
            lower_threshold, upper_threshold = (
                PLAN_TWO_LOWER_INTEREST_THRESHOLD,
                PLAN_TWO_UPPER_INTEREST_THRESHOLD,
            )

            # Minimum rate is RPI, applied to those earning below the lower threshold
            if self.user.annual_income <= lower_threshold:
                rate = RPI
            # Maximum rate is RPI + VIR, applied to those earning above the upper threshold
            elif self.user.annual_income >= upper_threshold:
                rate = RPI + PLAN_2_VIR
            # Intermediate rate is a sliding scale between RPI and RPI + VIR, applied to those earning between the lower and upper thresholds
            else:
                ratio = (self.user.annual_income - lower_threshold) / (
                    upper_threshold - lower_threshold
                )
                rate = RPI + (ratio * PLAN_2_VIR)
            return min(rate, effective_ceiling)

        # These are different names for the exact same loan product
        if self.loan_id == "plan_3" or self.loan_id == "postgraduate":
            return min(RPI + 0.03, effective_ceiling)

        if self.loan_id == "plan_5":
            return min(RPI, PREVAILING_MARKET_RATE_CAP)


class User:
    def __init__(
        self,
        user_id: str,
        annual_income: float,
        loans: List[UsersLoanProduct] = None,
    ):
        """The user of the SLC loan repayment calculator.

        Args:
            user_id (str): Internal name for the user, e.g. "user_1"
            annual_income (float): The user's annual income, e.g. 30000
            loans (List[UsersLoanProduct]): The user's loan products, e.g. personal plan_2 and postgraduate loans
        """
        self.user_id = user_id
        self.annual_income = annual_income
        self.loans = loans if loans else []


if __name__ == "__main__":
    pass
