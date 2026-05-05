"""main."""

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st

from core.calculations import freedom
from core.config import ConfigLoader
from core.loan_engine import User, UsersLoanProduct, Frequency
from core.simulation_engine import simulate

_cfg = ConfigLoader()


if __name__ == "__main__":
    USER = User(
        "james",
        annual_income=50_000,
    )

    plan_2_loan = UsersLoanProduct(
        user=USER,
        loan_id="plan_2",
        earnings_threshold=_cfg.earnings_threshold("plan_2"),
        repayment_period=int(_cfg.repayment_period("plan_2")),
        interest_application_window=Frequency.MONTHLY,
        balance=57_441.59,
        years_since_graduation=5,
    )
    USER.loans.append(plan_2_loan)

    plan_3_loan = UsersLoanProduct(
        user=USER,
        loan_id="plan_3",
        earnings_threshold=_cfg.earnings_threshold("plan_3"),
        repayment_period=int(_cfg.repayment_period("plan_3")),
        interest_application_window=Frequency.MONTHLY,
        balance=6_682.76,
        years_since_graduation=4,
    )
    USER.loans.append(plan_3_loan)

    result = simulate(
        USER,
        start_date=date(2026, 4, 1),
        salary_growth=Decimal("0.10"),
        to_df=True,
    )

    print(
        "Paid per plan: ",
        result.groupby("loan_id")["repayment_applied"].sum().to_dict(),
    )
    print(
        "Interest accrued per plan: ",
        result.groupby("loan_id")["interest_accrued"].sum().to_dict(),
    )
    print("Freedom date: ", freedom(result))
