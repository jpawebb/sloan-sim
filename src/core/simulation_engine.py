"""Monthly simulation loop for SLC student loan repayment."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

from core.config import ConfigLoader
from core.loan_engine import User, UsersLoanProduct
from core.models import LoanSimulation, MonthlyLedgerEntry, SimulationResult
from core.plans import get_plan

_cfg = ConfigLoader()

_UG_PLAN_PRIORITY: List[str] = ["plan_1", "plan_2", "plan_4", "plan_5"]
_PG_PLAN_IDS: frozenset[str] = frozenset({"plan_3"})


def _days_in_month(d: date) -> int:
    """Return the number of calendar days in the month of a given date."""
    return calendar.monthrange(d.year, d.month)[1]


def _advance_month(d: date) -> date:
    """Return the first day of the next month."""
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def _write_off_date(
    start_date: date, repayment_period: int, years_since_graduation: int
) -> date:
    """Compute the month on which a loan would be written off.

    The write-off occurs ``repayment_period - years_since_graduation`` full
    years after the ``start_date``.
    """
    remaining_years = repayment_period - years_since_graduation
    target_year = start_date.year + remaining_years
    return date(target_year, start_date.month, 1)


def _monthly_interest(balance: Decimal, annual_rate: Decimal, days: int) -> Decimal:
    """Calculate the interest for one month under the daily-accrual, monthly-application model.

    Formula: ``balance * (annual_rate / 365) * days``, rounded to the nearest penny using ROUND_HALF_UP
    (consistent with SLC's published methodology).
    """
    if balance <= 0 or annual_rate <= 0:
        return Decimal(0)
    return (balance * annual_rate / Decimal(365) * days).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _resolve_growth(salary_growth: Decimal | List[Decimal], year_index: int) -> Decimal:
    """Return the growth rate for the given anniversary year (0-indexed).

    If a list is provided and ``year_index`` exceeds its length, growth
    defaults to zero (salary frozen after the defined projection window).
    """
    if isinstance(salary_growth, list):
        if year_index < len(salary_growth):
            return Decimal(str(salary_growth[year_index]))
        return Decimal(0)
    return Decimal(str(salary_growth))


def simulate(
    user: User,
    start_date: date,
    salary_growth: Decimal | List(Decimal) = Decimal(0),
) -> SimulationResult:
    """Run a month-by-month simulation of the user's student loan repayments.

    Args:
        user: The borrower.  ``user.loans`` must be populated with one or more
            ``UsersLoanProduct`` instances before calling this function.
        start_date: The calendar month to begin the simulation from. The day component is ignored;
            the 1st of the month is always used.
        salary_growth: Annual salary growth rate as a single Decimal (e.g. 0.03 for 3% growth) or a list
            of per-year rates where index 0 applies afetr the first anniversary of the ``start_date``.
            Defaults to ``0.0`` (flat salary).

    Returns:
        A ``SimulationResult`` containing a per-loan ``LoanSimulation`` (with full monthly ledger)
        plus aggregate metrics.

    Raises:
        ValueError: If ``user.loans`` is empty.

    """
    if not user.loans:
        raise ValueError(
            "user.loans must contain at least one loan product to simulate."
        )

    current_date = start_date.replace(day=1)

    salary = Decimal(str(user.annual_income))

    balances: Dict[str, Decimal] = {
        loan.loan_id: Decimal(str(loan.balance)) for loan in user.loans
    }

    write_off_dates: Dict[str, date] = {
        loan.loan_id: _write_off_date(
            current_date,
            int(loan.repayment_period),
            loan.years_since_graduation,
        )
        for loan in user.loans
    }

    simulations: Dict[str, LoanSimulation] = {
        loan.loan_id: LoanSimulation(loan_id=loan.loan_id) for loan in user.loans
    }

    # Separate and sort loans by type-priority
    ug_loans: List[UsersLoanProduct] = sorted(
        [loan for loan in user.loans if loan.loan_id in set(_UG_PLAN_PRIORITY)],
        key=lambda l: _UG_PLAN_PRIORITY.index(l.loan_id),
    )
    pg_loans: List[UsersLoanProduct] = [
        loan for loan in user.loans if loan.loan_id in _PG_PLAN_IDS
    ]

    # Run sim until all loans are resolved or the last write-off date is reached,
    # whichever comes first
    max_write_off = max(write_off_dates.values())
    year_index = 0

    while current_date <= max_write_off:
        # Early exit if all loans are already resolved
        if all(bal <= 0 for bal in balances.values()):
            break

        days = _days_in_month(current_date)

        # 1. Calculate interest for every active loan
        interest_this_month: Dict[str, Decimal] = {}
        for loan in user.loans:
            lid = loan.loan_id
            # If the loan is already resolved, no interest
            if balances[lid] <= 0:
                interest_this_month[lid] = Decimal(0)
                continue

            # Apply interest according to the loan's effective annual rate for this month
            annual_rate = get_plan(lid).effective_interest_rate(user)
            interest_this_month[lid] = _monthly_interest(
                balances[lid], annual_rate, days
            )

        # 2. Compute repayments
        repayments: Dict[str, Decimal] = {lid: Decimal(0) for lid in balances}

        # Undergrad repaid first in order of plan priority (FR-4)
        active_ug = [l for l in ug_loans if balances[l.loan_id] > 0]
        if active_ug:
            primary_lid = active_ug[0].loan_id
            ug_threshold = _cfg.earnings_threshold(primary_lid, as_of=current_date)
            ug_pool = max(
                Decimal(0),
                (salary - ug_threshold)
                * Decimal(str(_cfg.repayment_rate(primary_lid)))
                / Decimal(12),
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Distribute the UG repayment pools
            remaining = ug_pool
            for loan in active_ug:
                if remaining <= 0:
                    break
                lid = loan.loan_id
                max_payable = balances[lid] + interest_this_month[lid]
                allocated = min(remaining, max_payable)
                repayments[lid] = allocated
                remaining -= allocated

        # Postgrad repaid after (FR-4)
        for loan in pg_loans:
            lid = loan.loan_id
            if balances[lid] <= 0:
                continue

            pg_threshold = _cfg.earnings_threshold(lid, as_of=current_date)
            pg_repayment = max(
                Decimal(0),
                (salary - pg_threshold)
                * Decimal(str(_cfg.repayment_rate(lid)))
                / Decimal(12),
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            repayments[lid] = min(
                pg_repayment, balances[lid] + interest_this_month[lid]
            )

        # 3. Update balances
        for loan in user.loans:
            lid = loan.loan_id
            opening = balances[lid]

            if opening <= 0:
                # Loan already resolved
                continue

            interest = interest_this_month[lid]
            repayment = repayments[lid]
            closing = opening + interest - repayment

            # Check for write-off
            written_off = False
            if current_date >= write_off_dates[lid] and closing > 0:
                written_off = True
                closing = Decimal(0)

            closing = max(Decimal(0), closing)
            balances[lid] = closing
            simulations[lid].ledger.append(
                MonthlyLedgerEntry(
                    month=current_date,
                    opening_balance=opening,
                    interest_accrued=interest,
                    repayment_applied=repayment,
                    closing_balance=closing,
                    written_off=written_off,
                )
            )

        # 4. Apply salary growth on anniversary
        next_date = _advance_month(current_date)
        if next_date.month == start_date.month and next_date.day == 1:
            growth = _resolve_growth(salary_growth, year_index)
            salary = salary * (1 + growth)
            year_index += 1

        current_date = next_date

    return SimulationResult(loans=simulations)
