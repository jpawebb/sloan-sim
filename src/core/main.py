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

# custom css
_CSS = """
<style>
/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d0d14;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] h2 {
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6b6b8a;
    margin-bottom: 0.5rem;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #12121c;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 14px 18px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6b6b8a !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 600;
}

/* ── Loan cards (st.container border=True) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #1e1e2e !important;
    border-radius: 10px !important;
    background: #12121c;
    padding: 4px 8px !important;
}

/* ── Tab bar ── */
[data-testid="stTabs"] button {
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6b6b8a;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #e2e2f0;
    border-bottom-color: #7c6af7 !important;
}

/* ── Run button ── */
.stButton > button[kind="primary"] {
    background: #7c6af7;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 0.5rem 1.5rem;
    transition: background 0.2s;
}
.stButton > button[kind="primary"]:hover {
    background: #6a57e0;
}

/* ── Loan sidebar expander header ── */
[data-testid="stExpander"] summary {
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    color: #a0a0c0;
}

/* ── General page background ── */
[data-testid="stAppViewContainer"] > .main {
    background: #0a0a12;
}
</style>
"""


def run():
    """Run the Streamlit app."""
    _cfg = ConfigLoader()

    st.set_page_config(
        page_title="Sloan-Sim",
        page_icon="💷",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject CSS
    st.markdown(_CSS, unsafe_allow_html=True)

    # page header
    st.markdown("## 💷 Sloan-Sim")
    st.caption("UK student loan repayment simulator")
    st.divider()

    # sidebar
    with st.sidebar:
        st.header("User Settings")

        user_name = st.text_input("Name", value="name")
        annual_income = st.number_input("Annual Income (£)", value=35_000, step=100)
        salary_growth = st.slider("Annual Salary Growth (%)", 0.0, 10.0, 2.0) / 100
        sim_start_date = st.date_input("Simulation Start Date", value=date(2026, 4, 1))

        st.divider()
        st.header("Loans")

        # add / remove loan buttons
        if "loan_count" not in st.session_state:
            st.session_state.loan_count = 2

        col_add, col_rem = st.columns(2)
        if col_add.button("＋ Add", use_container_width=True):
            st.session_state.loan_count += 1
        if (
            col_rem.button("－ Remove", use_container_width=True)
            and st.session_state.loan_count > 1
        ):
            removed_idx = st.session_state.loan_count - 1
            for _key in (
                f"id_{removed_idx}",
                f"bal_{removed_idx}",
                f"grad_{removed_idx}",
            ):
                st.session_state.pop(_key, None)
            st.session_state.loan_count -= 1

        # loan inputs
        loan_inputs: list[dict] = []
        for i in range(st.session_state.loan_count):
            with st.expander(f"Loan #{i + 1}", expanded=True):
                # Plan type + balance on the same row
                c1, c2 = st.columns([1, 1])
                l_id = c1.selectbox(
                    "Plan",
                    options=["plan_1", "plan_2", "plan_3", "plan_4", "plan_5"],
                    key=f"id_{i}",
                )
                l_bal = c2.number_input(
                    "Balance (£)",
                    min_value=0.0,
                    value=25_000.0,
                    step=500.0,
                    key=f"bal_{i}",
                )
                l_grad = st.number_input(
                    "Years since graduation",
                    min_value=0,
                    value=2,
                    key=f"grad_{i}",
                )
                loan_inputs.append(
                    {
                        "loan_id": l_id,
                        "balance": l_bal,
                        "years_since_graduation": l_grad,
                    }
                )

        st.divider()
        run_clicked = st.button(
            "▶ Run Simulation", type="primary", use_container_width=True
        )

    # main content
    if not run_clicked:
        st.info("Configure your loans in the sidebar, then click **▶ Run Simulation**.")
        st.stop()

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

        # tabs
        tab_summary, tab_loans, tab_chart, tab_data = st.tabs(
            ["📊  Summary", "🏦  Loan Breakdown", "📈  Chart", "📋  Raw Data"]
        )

        # summary
        with tab_summary:
            freedom_date = result.freedom_date
            overall_freedom = (
                freedom_date.strftime("%b %Y") if freedom_date else "Never"
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Repayments", f"£{result.total_repaid:,.2f}")
            m2.metric("Total Interest Added", f"£{result.total_interest_paid:,.2f}")
            m3.metric("Debt-Free Date", overall_freedom)
            m4.metric("Total Written Off", f"£{result.total_written_off:,.2f}")

        # loan breakdown
        with tab_loans:
            loan_items = list(result.loans.items())
            if not loan_items:
                st.info("No loan data returned by the simulation.")
            else:
                loan_cols = st.columns(len(loan_items))
                for i, (loan_id, sim) in enumerate(loan_items):
                    with loan_cols[i]:
                        with st.container(border=True):
                            # status badge
                            if sim.payoff_date:
                                is_write_off = any(e.written_off for e in sim.ledger)
                                method_label = (
                                    "Written Off" if is_write_off else "Paid Off"
                                )
                                method_color = "blue" if is_write_off else "green"
                            else:
                                method_label = "Not Free"
                                method_color = "red"
                                is_write_off = False

                            st.markdown(f"**{loan_id.upper()}**")
                            st.markdown(f":{method_color}[{method_label}]")

                            # amortization metric
                            if sim.ledger:
                                first_active = next(
                                    (e for e in sim.ledger if e.opening_balance > 0),
                                    None,
                                )
                                if first_active:
                                    net_change = (
                                        first_active.interest_accrued
                                        - first_active.repayment_applied
                                    )
                                    delta_str = (
                                        f"£{abs(net_change):,.2f} interest growth"
                                        if net_change > 0
                                        else f"£{abs(net_change):,.2f} net reduction"
                                    )
                                    st.metric(
                                        label="Monthly Net",
                                        value=(
                                            "Negative" if net_change > 0 else "Positive"
                                        ),
                                        delta=(
                                            f"+{delta_str}"
                                            if net_change > 0
                                            else f"-{delta_str}"
                                        ),
                                        delta_color=(
                                            "inverse" if net_change > 0 else "normal"
                                        ),
                                    )

                            # duration and early payoff
                            if sim.payoff_date:
                                original_loan = next(
                                    l for l in USER.loans if l.loan_id == loan_id
                                )
                                max_months = original_loan.repayment_period * 12
                                actual_months = len(sim.ledger)
                                dur_yrs, dur_mos = divmod(actual_months, 12)
                                st.caption(
                                    f"Cleared in {dur_yrs}y {dur_mos}m — {sim.payoff_date.strftime('%b %Y')}"
                                )
                                if not is_write_off:
                                    months_saved = max_months - actual_months
                                    if months_saved > 0:
                                        s_yrs, s_mos = divmod(months_saved, 12)
                                        st.success(f"⚡ {s_yrs}y {s_mos}m early!")

                            # financial summary
                            st.markdown(
                                f"**Paid:** £{sim.total_repaid:,.2f}  \n"
                                f"**Interest:** £{sim.total_interest_paid:,.2f}"
                                + (
                                    f"  \n**Forgiven:** £{sim.written_off_amount:,.2f}"
                                    if sim.written_off_amount > 0
                                    else ""
                                )
                            )

        # chart tab
        with tab_chart:
            chart_df = _simulation_to_dataframe(result)
            fig = px.area(
                chart_df,
                x="month",
                y="closing_balance",
                color="loan_id",
                title="Total Debt Projection",
                labels={"closing_balance": "Balance (£)", "month": "Date"},
                line_group="loan_id",
                template="plotly_dark",
                color_discrete_sequence=["#7c6af7", "#f76a8c", "#6af7c8", "#f7c46a"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
                legend_title_text="Loan",
                margin=dict(t=40, b=20, l=10, r=10),
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor="#1e1e2e")
            st.plotly_chart(fig, use_container_width=True)

        # raw data
        with tab_data:
            st.dataframe(
                _simulation_to_dataframe(result),
                use_container_width=True,
                hide_index=True,
            )

    except Exception as e:
        st.error(f"Simulation error: {e}")
