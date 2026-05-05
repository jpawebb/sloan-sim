"""SLC calculations, math helpers, and utilities."""

from typing import Mapping, Literal, TypedDict
import pandas as pd


class FreedomInfo(TypedDict):
    """Structured information about when and how a loan is considered 'free' (paid off or written off)."""

    date: pd.Timestamp | None
    method: Literal["paid_off", "written_off", "not_free"]


def freedom(df: pd.DataFrame) -> Mapping[str, FreedomInfo]:
    """Calculate when the user is free of each and all of their SLC loans, either by paying them off or them being written off.

    Args:
        df: A pandas DataFrame containing loan data, including columns for "loan_id", "closing_balance", and "month".

    Returns:
        A dictionary mapping loan IDs to their freedom date and method. Format:
        {
            "loan_id": {"date": datetime, "method": "paid_off" or "written_off"}
        }

    Example:
        >>> freedom(df)
        {
            "plan_2": {"date": datetime(2030, 4, 1), "method": "paid_off"},
            "plan_3": {"date": datetime(2040, 4, 1), "method": "written_off"}
        }

    """
    final_states = df.sort_values("month").groupby("loan_id").last()

    freedoms: dict[str, FreedomInfo] = {}

    for loan_id, row in final_states.iterrows():
        is_zero = row["closing_balance"] == 0
        is_written_off = row["is_written_off"]

        if is_zero:
            method = "written_off" if is_written_off else "paid_off"
            date = row["month"]
        else:
            method = "not_free"
            date = None

        freedoms[str(loan_id)] = {"date": date, "method": method}

    return freedoms
