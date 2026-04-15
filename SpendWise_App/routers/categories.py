from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import col, select, func
from ..models import ExpensesDB, UserDetails, ExpenseItem, CategorySummary, MonthlyCategoryDB
from ..database import SessionDependency
from ..oauth2 import get_current_active_user
from typing import Annotated
from ..utils.general import get_date_filter
from datetime import date

router = APIRouter(prefix="/categories", tags=["Categories"])

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]

CATEGORIES = ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare"]

# @router.get("/", response_model=list[CategorySummary])
# def get_expenses_by_category(
#     db: SessionDependency,
#     current_user: CurrentUser,
#     period: str = Query(default="all_time")
# ):
#     """
#     For this_month, this_year, last_6_months → aggregate from MonthlyCategoryDB (fast).
#     For all_time → sum all MonthlyCategoryDB records.
#     Individual expense items always pulled from ExpensesDB.
#     """
#     if current_user.Id is None:
#         raise HTTPException(status_code=400, detail="User ID not found")

#     since = get_date_filter(period)

#     # 1. Get aggregated totals from MonthlyCategoryDB
#     monthly_query = select(MonthlyCategoryDB).where(
#         MonthlyCategoryDB.UserId == current_user.Id
#     )
#     if since:
#         monthly_query = monthly_query.where(
#             col(MonthlyCategoryDB.Month) >= since.strftime("%Y-%m")
#         )
#     monthly_records = db.exec(monthly_query).all()

#     # Sum up totals per category across all matching months
#     totals = {cat: 0.0 for cat in CATEGORIES}
#     for record in monthly_records:
#         for cat in CATEGORIES:
#             totals[cat] = round(totals[cat] + float(getattr(record, cat)), 2)

#     # 2. Get individual expense items from ExpensesDB
#     expense_query = select(ExpensesDB).where(
#         ExpensesDB.UserId == current_user.Id
#     )
#     if since:
#         expense_query = expense_query.where(ExpensesDB.DatePurchased >= since)

#     expense_query = expense_query.order_by(col(ExpensesDB.DatePurchased).desc())
#     expenses = db.exec(expense_query).all()

#     # 3. Group individual items by category
#     items_map: dict[str, list[ExpenseItem]] = {cat: [] for cat in CATEGORIES}
#     for expense in expenses:
#         cat = expense.Type
#         if cat in items_map:
#             items_map[cat].append(ExpenseItem.model_validate(expense))

#     # 4. Build response — only include categories with spending
#     return [
#         CategorySummary(category=cat, total=totals[cat], expenses=items_map[cat])
#         for cat in CATEGORIES
#         if totals[cat] > 0
#     ]


# @router.get("/{category}", response_model=CategorySummary)
# def get_single_category(
#     category: str,
#     db: SessionDependency,
#     current_user: CurrentUser,
#     period: str = Query(default="all_time")
# ):
#     if current_user.Id is None:
#         raise HTTPException(status_code=400, detail="User ID not found")

#     since = get_date_filter(period)

#     # 1. Get total from MonthlyCategoryDB
#     monthly_query = select(MonthlyCategoryDB).where(
#         MonthlyCategoryDB.UserId == current_user.Id
#     )
#     if since:
#         monthly_query = monthly_query.where(
#             col(MonthlyCategoryDB.Month) >= since.strftime("%Y-%m")
#         )
#     monthly_records = db.exec(monthly_query).all()

#     # Find the matching category field (case-insensitive)
#     matched_cat = next((c for c in CATEGORIES if c.lower() == category.lower()), None)
#     if not matched_cat:
#         raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

#     total = round(sum(float(getattr(r, matched_cat)) for r in monthly_records), 2)

#     # 2. Get individual items from ExpensesDB
#     expense_query = (
#         select(ExpensesDB)
#         .where(ExpensesDB.UserId == current_user.Id)
#         .where(func.lower(ExpensesDB.Type) == category.lower())
#     )
#     if since:
#         expense_query = expense_query.where(ExpensesDB.DatePurchased >= since)

#     expenses = db.exec(expense_query.order_by(col(ExpensesDB.DatePurchased).desc())).all()

#     return CategorySummary(
#         category=matched_cat,
#         total=total,
#         expenses=[ExpenseItem.model_validate(e) for e in expenses]
#     )
# @router.get("/", response_model=list[CategorySummary])
# def get_expenses_by_category(db: SessionDependency, current_user: CurrentUser, period: str = Query(default="all_time")):
#     since = get_date_filter(period)
#     query = select(ExpensesDB).where(ExpensesDB.UserId == current_user.Id)

#     if since:
#         query = query.where(ExpensesDB.DatePurchased >= since)

#     query = query.order_by(ExpensesDB.Type, col(ExpensesDB.DatePurchased).desc())
#     expenses = db.exec(query).all()

#     category_map: dict[str, CategorySummary] = {}
#     for expense in expenses:
#         cat = expense.Type
#         if cat not in category_map:
#             category_map[cat] = CategorySummary(category=cat, total=0.0, expenses=[])
#         category_map[cat].total = round(category_map[cat].total + expense.AmountSpent, 2)
#         category_map[cat].expenses.append(ExpenseItem.model_validate(expense))

#     return list(category_map.values())
@router.get("/", response_model=list[CategorySummary])
def get_expenses_by_category(db: SessionDependency, current_user: CurrentUser, period: str = Query(default="all_time")):
    from ..models import PreviousExpenseDB
    since = get_date_filter(period)

    # ── 1. Day-to-day expenses from ExpensesDB ──
    query = select(ExpensesDB).where(ExpensesDB.UserId == current_user.Id)
    if since:
        query = query.where(ExpensesDB.DatePurchased >= since)
    query = query.order_by(ExpensesDB.Type)
    expenses = db.exec(query).all()

    category_map: dict[str, CategorySummary] = {}
    for expense in expenses:
        cat = expense.Type
        if cat == "Food & Dining":
            cat = "Food"
        if cat not in category_map:
            category_map[cat] = CategorySummary(category=cat, total=0.0, expenses=[])
        category_map[cat].total = round(category_map[cat].total + expense.AmountSpent, 2)
        category_map[cat].expenses.append(ExpenseItem.model_validate(expense))

    # ── 2. Imported expenses from PreviousExpenseDB ──
    prev_query = select(PreviousExpenseDB).where(PreviousExpenseDB.UserId == current_user.Id)
    if since:
        # PreviousExpenseDB.Month is "YYYY-MM" string so filter by year-month
        since_month = since.strftime("%Y-%m")
        prev_query = prev_query.where(PreviousExpenseDB.Month >= since_month)
    prev_records = db.exec(prev_query).all()

    # Each month record becomes one summary ExpenseItem per category
    imported_categories = ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare"]
    for record in prev_records:
        for cat in imported_categories:
            amount = getattr(record, cat)
            if amount <= 0:
                continue
            if cat not in category_map:
                category_map[cat] = CategorySummary(category=cat, total=0.0, expenses=[])
            category_map[cat].total = round(category_map[cat].total + amount, 2)
            # Add as a single summary line with a fake Id (-record.Id to avoid collision)
            category_map[cat].expenses.append(ExpenseItem(
                Id=-(record.Id or 0),
                ItemName=f"Imported ({record.Month})",
                AmountSpent=amount,
                DatePurchased=date(int(record.Month[:4]), int(record.Month[5:]), 1),
                Note="Imported expense",
                Type=cat
            ))

    # Sort all expenses within each category by date descending
    for summary in category_map.values():
        summary.expenses.sort(key=lambda e: e.DatePurchased, reverse=True)

    return list(category_map.values())


@router.get("/{category}", response_model=CategorySummary)
def get_single_category(
    category: str,
    db: SessionDependency,
    current_user: CurrentUser,
    period: str = Query(default="all_time")
):
    since = get_date_filter(period)
    query = (
        select(ExpensesDB)
        .where(ExpensesDB.UserId == current_user.Id)
        .where(func.lower(ExpensesDB.Type) == category.lower())
    )

    if since:
        query = query.where(ExpensesDB.DatePurchased >= since)

    expenses = db.exec(query.order_by(col(ExpensesDB.DatePurchased).desc())).all()
    total = round(sum(e.AmountSpent for e in expenses), 2)

    return CategorySummary(
        category=category,
        total=total,
        expenses=[ExpenseItem.model_validate(e) for e in expenses]
    )
