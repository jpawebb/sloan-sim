"""Module for instantiating and managing loan plans."""

from core.plans.base import LoanPlan
from core.plans.plan_1 import Plan1
from core.plans.plan_2 import Plan2
from core.plans.plan_3 import Plan3
from core.plans.plan_4 import Plan4
from core.plans.plan_5 import Plan5


def _build_registry() -> dict[str, LoanPlan]:
    """Build a registry of all loan plans."""
    registry: dict[str, LoanPlan] = {}
    for cls in (Plan1, Plan2, Plan3, Plan4, Plan5):
        instance = cls()
        registry[cls.loan_id] = instance
        for alias in cls.aliases:
            registry[alias] = instance
    return registry


PLAN_REGISTRY: dict[str, LoanPlan] = _build_registry()


def get_plan(loan_id: str) -> LoanPlan:
    """Get a loan plan by its ID or alias."""
    try:
        return PLAN_REGISTRY[loan_id]
    except KeyError as e:
        raise ValueError(f"Unknown loan plan: {loan_id}") from e
