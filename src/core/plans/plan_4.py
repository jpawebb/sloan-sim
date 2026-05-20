"""SLC Plan 4 implementation."""

from decimal import Decimal
from datetime import date

from src.core.config import ConfigLoader
from .base import LoanPlan

_cfg = ConfigLoader()


class Plan4(LoanPlan):
    """SLC Plan 4 implementation. Earnings threshold has changed from £32,745 in 2025/26 to £33,795 in 2026/27."""

    loan_id = "plan_4"

    def effective_interest_rate(self, user, as_of: date = None) -> Decimal:
        """Effective rate is the lower of RPI and the Bank of England (BOE) base rate + 1%."""
        if as_of == None:
            as_of = date.today()

        rpi = _cfg.rpi(as_of=as_of)
        boe_base = _cfg.boe_base_rate(as_of=as_of)

        return min(rpi, boe_base + Decimal(0.01))
