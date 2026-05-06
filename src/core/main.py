"""main."""

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st
import plotly.express as px

from .config import ConfigLoader
from .loan_engine import User, UsersLoanProduct, Frequency
from .simulation_engine import simulate, _simulation_to_dataframe


def run():
    """Run the Streamlit app."""
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
            removed_idx = st.session_state.loan_count - 1
            for _key in (
                f"id_{removed_idx}",
                f"bal_{removed_idx}",
                f"grad_{removed_idx}",
            ):
                st.session_state.pop(_key, None)
            st.session_state.loan_count -= 1

        loan_inputs = []

        # Generate dynamic inputs
        for i in range(st.session_state.loan_count):
            with st.expander(f"Loan #{i + 1}", expanded=True):
                l_id = st.selectbox(
                    "Plan Type",
                    options=["plan_1", "plan_2", "plan_3", "plan_4", "plan_5"],
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
                    {
                        "loan_id": l_id,
                        "balance": l_bal,
                        "years_since_graduation": l_grad,
                    }
                )

        st.divider()

    if st.button("Run Full Simulation", type="primary"):
        if sim_start_date is None:
            st.error("Please set a simulation start date before running.")
            st.stop()

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
            )

            ############################
            #     Simulation stats     #
            ############################
            st.divider()
            st.subheader("Simulation Summary")

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Total Repayments", f"£{result.total_repaid:,.2f}")
            m_col2.metric("Total Interest Added", f"£{result.total_interest_paid:,.2f}")

            # Overall freedom date logic
            freedom_date = result.freedom_date
            overall_freedom = (
                freedom_date.strftime("%b %Y") if freedom_date else "Never"
            )
            m_col3.metric("Debt Free Date", overall_freedom)

            # New insight from the model expansion
            m_col4.metric("Total Written Off", f"£{result.total_written_off:,.2f}")

            st.divider()

            st.write("### Loan Specifics")

            # Dynamically create columns for each loan in the result
            loan_items = list(result.loans.items())
            if not loan_items:
                st.info("No loan data returned by the simulation.")
            else:
                loan_cols = st.columns(len(loan_items))

                for i, (loan_id, sim) in enumerate(loan_items):
                    with loan_cols[i]:
                        if sim.payoff_date:
                            is_write_off = any(e.written_off for e in sim.ledger)
                            method_label = "Written Off" if is_write_off else "Paid Off"
                            method_color = "blue" if is_write_off else "green"
                        else:
                            method_label = "Not Free"
                            method_color = "red"

                        st.markdown(f"**{loan_id.upper()}**")

                        st.markdown(f":{method_color}[{method_label}]")

                        if sim.payoff_date:
                            original_loan = next(
                                l for l in USER.loans if l.loan_id == loan_id
                            )
                            max_months = original_loan.repayment_period * 12
                            actual_months = len(sim.ledger)

                            # Calculate Years/Months for the duration
                            dur_yrs, dur_mos = divmod(actual_months, 12)
                            st.caption(
                                f"Cleared in {dur_yrs} years {dur_mos} months, on {sim.payoff_date.strftime('%B %Y')}"
                            )

                            if not is_write_off:
                                months_saved = max_months - actual_months
                                if months_saved > 0:
                                    s_yrs, s_mos = divmod(months_saved, 12)
                                    st.success(f"{s_yrs} years {s_mos} months early!")

                        # 4. Individual Stats (replaces groupby().to_dict() lookups)
                        st.write(f"Paid: £{sim.total_repaid:,.2f}")
                        st.write(f"Int: £{sim.total_interest_paid:,.2f}")

                        # Optional: New detail on how much was forgiven
                        if sim.written_off_amount > 0:
                            st.write(f"Forgiven: £{sim.written_off_amount:,.2f}")
            st.divider()

            ####################
            #     Visuals      #
            ####################
            chart_df = _simulation_to_dataframe(result)
            fig_mountain = px.area(
                chart_df,
                x="month",
                y="closing_balance",
                color="loan_id",
                title="Total Debt Projection",
                labels={"closing_balance": "Balance (£)", "month": "Year"},
                line_group="loan_id",
            )
            st.plotly_chart(fig_mountain, width="stretch")

            with st.expander("Show Monthly Raw Data"):
                st.dataframe(_simulation_to_dataframe(result))

        except Exception as e:
            st.error(f"Error in configuration: {e}")
