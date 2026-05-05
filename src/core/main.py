"""main."""

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st
import plotly.express as px

from calculations import freedom
from config import ConfigLoader
from loan_engine import User, UsersLoanProduct, Frequency
from simulation_engine import simulate

_cfg = ConfigLoader()

st.set_page_config(page_title="Sloan-Sim Dashboard", layout="wide")

st.title("Sloan-Sim")

with st.sidebar:
    st.header("User Settings")
    user_name = st.text_input("User", value="name")
    annual_income = st.number_input("Annual Income (£)", value=35000, step=100)
    salary_growth = st.slider("Annual Salary Growth (%)", 0.0, 10.0, 2.0) / 100
    sim_start_date = st.date_input("Simulation Start Date", value=date(2026, 4, 1))

    if "loan_count" not in st.session_state:
        st.session_state.loan_count = 2

    col_add, col_rem = st.columns(2)
    if col_add.button("Add Loan"):
        st.session_state.loan_count += 1
    if col_rem.button("Remove") and st.session_state.loan_count > 1:
        st.session_state.loan_count -= 1

    loan_inputs = []

    # Generate dynamic inputs
    for i in range(st.session_state.loan_count):
        with st.expander(f"Loan #{i+1}", expanded=True):
            l_id = st.selectbox(
                "Plan Type",
                options=["plan_1", "plan_2", "plan_3", "plan_4", "plan_5", "postgrad"],
                key=f"id_{i}",
            )
            l_bal = st.number_input(
                "Current Balance (£)",
                min_value=0.0,
                value=25000.0,
                step=500.0,
                key=f"bal_{i}",
            )
            l_grad = st.number_input(
                "Years Since Grad", min_value=0, value=2, key=f"grad_{i}"
            )
            loan_inputs.append(
                {"loan_id": l_id, "balance": l_bal, "years_since_graduation": l_grad}
            )

    st.divider()

if st.button("Run Full Simulation", type="primary"):

    USER = User(user_name, annual_income=annual_income)

    try:
        for row in loan_inputs:
            loan = UsersLoanProduct(
                user=USER,
                loan_id=row["loan_id"],
                earnings_threshold=_cfg.earnings_threshold(row["loan_id"]),
                repayment_period=int(_cfg.repayment_period(row["loan_id"])),
                interest_application_window=Frequency.MONTHLY,
                balance=Decimal(str(row["balance"])),
                years_since_graduation=row["years_since_graduation"],
            )
            USER.loans.append(loan)

        result = simulate(
            USER,
            start_date=sim_start_date,
            salary_growth=Decimal(str(salary_growth)),
            to_df=True,
        )

        ############################
        #     Simulation stats     #
        ############################
        paid_by_loan = result.groupby("loan_id")["repayment_applied"].sum().to_dict()
        interest_by_loan = result.groupby("loan_id")["interest_accrued"].sum().to_dict()
        freedom_stats = freedom(result)

        st.divider()

        st.subheader("Simulation Summary")

        total_paid = sum(paid_by_loan.values())
        total_interest = sum(interest_by_loan.values())

        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Total Repayments", f"£{total_paid:,.2f}")
        m_col2.metric("Total Interest Added", f"£{total_interest:,.2f}")

        # Calculate overall freedom (the date the last loan is cleared)
        all_dates = [f["date"] for f in freedom_stats.values() if f["date"] is not None]
        overall_freedom = max(all_dates).strftime("%b %Y") if all_dates else "Never"
        m_col3.metric("Debt Free Date", overall_freedom)

        st.divider()

        st.write("### 🎓 Loan Specifics")

        # Create a column for each loan to show its individual "fate"
        loan_cols = st.columns(len(freedom_stats))

        for i, (loan_id, info) in enumerate(freedom_stats.items()):
            with loan_cols[i]:
                # Style based on method
                method_label = info["method"].replace("_", " ").title()
                method_color = "green" if info["method"] == "paid_off" else "blue"
                if info["method"] == "not_free":
                    method_color = "red"

                st.markdown(f"**{loan_id.upper()}**")

                # Display status as a little "badge" using markdown
                st.markdown(f":{method_color}[{method_label}]")

                if info["date"]:
                    st.caption(f"Cleared: {info['date'].strftime('%B %Y')}")

                # Show individual stats for this loan
                loan_paid = paid_by_loan.get(loan_id, 0)
                loan_int = interest_by_loan.get(loan_id, 0)

                st.write(f"Paid: £{loan_paid:,.2f}")
                st.write(f"Int: £{loan_int:,.2f}")

        st.divider()

        ####################
        #     Visuals      #
        ####################
        fig_mountain = px.area(
            result,
            x="month",
            y="closing_balance",
            color="loan_id",
            title="Total Debt Projection",
            labels={"closing_balance": "Balance (£)", "month": "Year"},
            line_group="loan_id",
        )
        st.plotly_chart(fig_mountain, width="stretch")

        with st.expander("Show Monthly Raw Data"):
            st.dataframe(result)

    except Exception as e:
        st.error(f"Error in configuration: {e}")
