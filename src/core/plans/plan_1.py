"""SLC Plan 1 implementation."""

from decimal import Decimal
from datetime import date

from src.core.config import ConfigLoader
from .base import LoanPlan

_cfg = ConfigLoader()


class Plan1(LoanPlan):
    """SLC Plan 1 implementation. Earnings threshold has changed from £26,065 in 2025/26 to £26,900 in 2026/27."""

    loan_id = "plan_1"

    def effective_interest_rate(self, user, as_of: date = None) -> Decimal:
        """Effective rate is the lower of RPI and the Bank of England (BOE) base rate + 1%."""
        if as_of == None:
            as_of = date.today()

        # Dynamic chronological lookups from config.toml
        rpi = _cfg.rpi(as_of=as_of)
        boe_base = _cfg.boe_base_rate(as_of=as_of)

        return min(rpi, boe_base + Decimal(0.01))
