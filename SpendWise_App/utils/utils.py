# code for utility functions 
    # hasing of pw
    # verification of pw
# so that imports and code is not repeated in multiple files/main file 

import re
from typing import Any, Type, Union
from fastapi import HTTPException
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import SQLModel, Session, extract, func, select
from .calculations import calculate_pir, calculate_shares
from ..models import BasketCategoryDB, BasketDB, ExpensesDB, MonthlyCategoryDB, PreviousExpenseDB, UserBudgetDB
from datetime import date, timedelta

def update_monthly_totals(db: Session, user_id: int, target_date: date | None, source_model: Any):
    config = {
        BasketDB: {"summary_table": BasketCategoryDB, "use_date": False},
        ExpensesDB: {"summary_table": MonthlyCategoryDB, "use_date": True}
    }
    
    cfg = config[source_model]
    SummaryTable = cfg["summary_table"]

    # 1. Build Aggregate Query
    query = select(source_model.Type, func.sum(source_model.AmountSpent)).where(source_model.UserId == user_id)

    if cfg["use_date"] and target_date:
        start = target_date.replace(day=1)
        next_m = (start + timedelta(days=32)).replace(day=1)
        query = query.where(source_model.DatePurchased >= start, source_model.DatePurchased < next_m)

    # 2. Execute and map results
    results = db.exec(query.group_by(source_model.Type)).all()
    # Handle potential None values from sum
    new_totals = {cat: float(amt) if amt else 0.0 for cat, amt in results}

    # 3. Upsert Summary Record
    summary_stmt = select(SummaryTable).where(SummaryTable.UserId == user_id)
    month_str = target_date.strftime("%Y-%m") if (target_date and cfg["use_date"]) else None
    
    if month_str:
        summary_stmt = summary_stmt.where(SummaryTable.Month == month_str)

    record = db.exec(summary_stmt).first()

    if not record:
        init_data: dict[str, Any] = {"UserId": user_id}
        init_data = {"UserId": user_id}
        if month_str:
            init_data["Month"] = month_str
        record = SummaryTable(**init_data)
        db.add(record)
    
    # 4. Update Category Columns
    # Assuming your model columns match these exactly
    fields = ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]
    for field in fields:
        setattr(record, field, new_totals.get(field, 0.0))

    # Note: db.commit() removed to allow the router to control the transaction
    
def calculate_pir_for_user(user_id: int, now: date, session: Session) -> float:
    """
    Builds the items list for calculate_pir() by comparing:
      - base period    = 2 months ago (P0)
      - current period = last month   (Pt)
    Weight = how much user spent on that category in the base period.
    """
    base_month    = (now.replace(day=1) - timedelta(days=1)).replace(day=1)  # 2 months ago
    current_month = now.replace(day=1) - timedelta(days=1)                   # last month
    current_month = current_month.replace(day=1)

    def fetch_category_totals(year: int, month: int) -> dict[str, float]:
        expenses = session.exec(
            select(ExpensesDB).where(
                ExpensesDB.UserId == user_id,
                extract("month", ExpensesDB.DatePurchased) == month,
                extract("year",  ExpensesDB.DatePurchased) == year,
            )
        ).all()
        totals: dict[str, float] = {}
        for e in expenses:
            totals[e.Type] = totals.get(e.Type, 0) + e.AmountSpent
        return totals

    base_totals    = fetch_category_totals(base_month.year,    base_month.month)
    current_totals = fetch_category_totals(current_month.year, current_month.month)

    # Only include categories that exist in BOTH periods
    shared_categories = set(base_totals.keys()) & set(current_totals.keys())
    if not shared_categories:
        return 0.0

    items = [
        {
            "name":          cat,
            "base_price":    base_totals[cat],
            "current_price": current_totals[cat],
            "weight":        base_totals[cat],  # base-period spending = Laspeyres weight
        }
        for cat in shared_categories
    ]

    try:
        return calculate_pir(items)
    except ValueError:
        return 0.0


def get_monthly_category_totals(db: Session, user_id: int, target_date: date) -> dict[str, float]:
    # 1. Convert the date into your standard YYYY-MM string
    month_str = target_date.strftime("%Y-%m")
    
    # 2. Fetch the pre-calculated summary row
    monthly_record = db.exec(
        select(MonthlyCategoryDB)
        .where(MonthlyCategoryDB.UserId == user_id)
        .where(MonthlyCategoryDB.Month == month_str)
    ).first()
    
    # 3. Handle the case where the user has no expenses for this month yet
    if not monthly_record:
        return {
            "Food": 0.0, "Transport": 0.0, "Utilities": 0.0, 
            "Entertainment": 0.0, "Shopping": 0.0, "Healthcare": 0.0, "Other": 0.0
        }

    # 4. Return as a dictionary (note: cast to float for precision)
    return {
        "Food": float(monthly_record.Food),
        "Transport": float(monthly_record.Transport),
        "Utilities": float(monthly_record.Utilities),
        "Entertainment": float(monthly_record.Entertainment),
        "Shopping": float(monthly_record.Shopping),
        "Healthcare": float(monthly_record.Healthcare),
        "Other": float(monthly_record.Other)
    }

def get_best_base_shares(db: Session, user_id: int, current_month: str) -> tuple[dict[str, float], str]:
    """
    Attempts to find the best possible base month for comparison.
    """
    # 1. Try Year-on-Year (12 months ago)
    year, month = map(int, current_month.split("-"))
    yoy_month = f"{year-1}-{month:02d}"
    
    base_record_db = db.exec(
        select(PreviousExpenseDB)
        .where(PreviousExpenseDB.UserId == user_id, PreviousExpenseDB.Month == yoy_month)
    ).first()

    # 2. Fallback: Try the most recent available month before current_month
    if not base_record_db:
        base_record_db = db.exec(
            select(PreviousExpenseDB)
            .where(PreviousExpenseDB.UserId == user_id, PreviousExpenseDB.Month < current_month)
            .order_by(PreviousExpenseDB.Month.desc())
        ).first()

    if not base_record_db:
        raise HTTPException(status_code=404, detail="Not enough past data (calc base)")
    # Convert record to totals and then to shares
    base_record = {
        "Food": base_record_db.Food,
        "Transport": base_record_db.Transport,
        "Utilities": base_record_db.Utilities,
        "Entertainment": base_record_db.Entertainment,
        "Shopping": base_record_db.Shopping,
        "Healthcare": base_record_db.Healthcare
    }
    base_month = base_record_db.Month
    return calculate_shares(base_record), base_month

# Fetches the user's budget row, creating a default (AutoBudget=True) if none exists.
def get_or_create_budget(user_id: int, session: Session) -> UserBudgetDB:
    # from SpendWise_App.models import UserBudgetDB  # local to avoid circular import

    budget = session.exec(
        select(UserBudgetDB).where(UserBudgetDB.UserId == user_id)
    ).first()

    if not budget:
        budget = UserBudgetDB(
            UserId=user_id,
            AutoBudget=True,
            TotalBudget=0,
            Food=0, Transport=0, Utilities=0,
            Entertainment=0, Shopping=0, Healthcare=0, Other=0
        )
        session.add(budget)
        session.commit()
        session.refresh(budget)

    return budget






