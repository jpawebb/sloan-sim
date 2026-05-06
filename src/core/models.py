"""Dataclasses for simulation outputs."""

from __future__ import annotations

from typing import Dict, List
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class MonthlyLedgerEntry:
    """A single month's snapshot, for one loan.

    Attributes:
        month: The first day of the simulated month.
        opening_balance: The balance at the start of the month, before interest or repayments.
        interest_accrued: Interest added to the balance this month.
        repayment_applied: Amount deducted from the balance this month.
        closing_balance: Balance at end of the month after interest and repayments.
        written_off: True if the loan was forgiven at the end of the month.

    """

    month: date
    opening_balance: Decimal
    interest_accrued: Decimal
    repayment_applied: Decimal
    closing_balance: Decimal
    written_off: bool = False


@dataclass
class LoanSimulation:
    """Full simulation history for a single loan.

    Attributes:
        loan_id: The plan identifier, e.g. ``"plan_2"``.
        ledger: Chronological list of monthly entries.

    """

    loan_id: str
    ledger: List[MonthlyLedgerEntry] = field(default_factory=list)

    @property
    def total_interest_paid(self) -> Decimal:
        """Sum of all interest accrued over the simulation lifetime."""
        return sum((e.interest_accrued for e in self.ledger), Decimal(0))

    @property
    def total_repaid(self) -> Decimal:
        """Sum of all repayments applied over the simulation lifetime."""
        return sum((e.repayment_applied for e in self.ledger), Decimal(0))

    @property
    def payoff_date(self) -> date | None:
        """First month the balance reaches zero (paid off or forgiven)."""
        for entry in self.ledger:
            if entry.closing_balance <= 0:
                return entry.month
        return None

    @property
    def cost_ratio(self) -> Decimal:
        """The ratio of total interest to the original balance.

        Shows how 'expensive' the debt was (e.g., 0.5 means you paid 50% extra in interest).
        """
        if not self.ledger:
            return Decimal(0)
        original_balance = self.ledger[0].opening_balance
        if original_balance <= 0:
            return Decimal(0)
        return (self.total_interest_paid / original_balance).quantize(Decimal("0.0001"))

    @property
    def is_fully_repaid(self) -> bool:
        """True if the loan was paid off by the user; False if it was written off."""
        return any(e.closing_balance <= 0 and not e.written_off for e in self.ledger)

    @property
    def written_off_amount(self) -> Decimal:
        """Balance forgiven at write-off, or zero if loan was fully repaid."""
        for entry in self.ledger:
            if entry.written_off:
                return (
                    entry.opening_balance
                    + entry.interest_accrued
                    - entry.repayment_applied
                )
        return Decimal(0)

    @property
    def resolution_status(self) -> str:
        """Human-readable final state of the loan."""
        if not self.ledger or self.ledger[-1].closing_balance > 0:
            return "Active"
        return "Written Off" if any(e.written_off for e in self.ledger) else "Paid Off"


@dataclass
class SimulationResult:
    """Aggregate simulation output across all of a user's loans.

    Attributes:
        loans: Per-loan simulation outputs.

    """

    loans: Dict[str, LoanSimulation]

    @property
    def total_interest_paid(self) -> Decimal:
        """Total interest paid across all loans."""
        return sum((s.total_interest_paid for s in self.loans.values()), Decimal(0))

    @property
    def total_repaid(self) -> Decimal:
        """Total amount repaid across all loans."""
        return sum((s.total_repaid for s in self.loans.values()), Decimal(0))

    @property
    def freedom_date(self) -> date | None:
        """The month all loans are cleared or written off, i.e. the "freedom date".

        Returns ``None`` if any loan was never resolved (should not happen in a well-formed simulation).
        """
        dates = [s.payoff_date for s in self.loans.values()]
        if any(d is None for d in dates):
            return None
        return max(dates)

    @property
    def total_written_off(self) -> Decimal:
        """Sum of all balances forgiven across all loans."""
        return sum((s.written_off_amount for s in self.loans.values()), Decimal(0))

    @property
    def weighted_interest_rate_impact(self) -> Decimal:
        """Total interest paid as a percentage of total principal repaid.

        Useful for showing the 'real' cost of the borrowing bundle.
        """
        if self.total_repaid == 0:
            return Decimal(0)
        return (self.total_interest_paid / self.total_repaid).quantize(
            Decimal("0.0001")
        )

    @property
    def peak_debt(self) -> Decimal:
        """The highest combined balance at any point in the simulation."""
        # Find all unique months across all loans
        all_months = sorted({e.month for s in self.loans.values() for e in s.ledger})

        max_total = Decimal(0)
        for m in all_months:
            month_total = sum(
                next((e.opening_balance for e in s.ledger if e.month == m), Decimal(0))
                for s in self.loans.values()
            )
            max_total = max(max_total, month_total)
        return max_total

    def get_summary_table(self) -> List[Dict]:
        """Generate a clean list of dicts for pd.DataFrame or st.table consumption."""
        return [
            {
                "Loan": lid,
                "Status": sim.resolution_status,
                "Total Repaid": sim.total_repaid,
                "Total Interest": sim.total_interest_paid,
                "Written Off": sim.written_off_amount,
                "Freedom Date": (
                    sim.payoff_date.strftime("%Y-%m") if sim.payoff_date else "N/A"
                ),
            }
            for lid, sim in self.loans.items()
        ]
