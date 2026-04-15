from typing import Annotated
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import col, extract, select
from ..utils.utils import calculate_pir_for_user, get_monthly_category_totals
from ..utils.calculations import calculate_forecast, calculate_realtime_savings, calculate_shares, compute_tornqvist_pir
from ..models import *
from ..database import SessionDependency
from ..oauth2 import get_current_active_user

router = APIRouter(
    prefix="/dashboard", 
    tags=["dashboard"]
    )

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]

# budget progess and savings this month 
@router.get("/summary")
def get_dashboard_summary(current_user: CurrentUser, session: SessionDependency):
    now = date.today()

    this_month_expenses = session.exec(
        select(ExpensesDB).where(
            ExpensesDB.UserId == current_user.Id,
            extract("month", ExpensesDB.DatePurchased) == now.month,
            extract("year", ExpensesDB.DatePurchased) == now.year,
        )
    ).all()
    total_spent = sum(e.AmountSpent for e in this_month_expenses)

    budget = session.exec(
        select(UserBudgetDB).where(UserBudgetDB.UserId == current_user.Id)
    ).first()

    settings = session.exec(
        select(UserSettingsDB).where(UserSettingsDB.UserId == current_user.Id)
    ).first()

    total_budget = budget.TotalBudget if budget else 0
    monthly_income = settings.MonthlyIncome if settings else 0


    savings = calculate_realtime_savings(
        monthly_income=monthly_income,
        current_total_spending=total_spent,
        reference_date=now
    )

    if savings < 0 and settings and settings.BudgetThresholdAlerts:
        create_alert_internal(
            session,
            current_user.Id,
            "Overspending Alert",
            "You are overspending this month",
            "danger"
        )

    budget_percent = round(total_spent / total_budget * 100, 1) if total_budget else 0

    if total_budget and settings and settings.BudgetThresholdAlerts:
        threshold = settings.AlertThreshold if settings.AlertThreshold else 80

        if budget_percent >= 100:
            create_alert_internal(
                session,
                current_user.Id,
                "Budget Exceeded",
                "You exceeded your budget!",
                "danger"
            )
        elif budget_percent >= threshold:
            create_alert_internal(
                session,
                current_user.Id,
                "Budget Warning",
                f"You have used {budget_percent}% of your budget.",
                "warning"
            )
    return {

        "total_spent": round(total_spent, 2),
        "total_budget": total_budget,
        "budget_percent": budget_percent,
        "savings": savings,
    }

# inflation rates 
@router.get("/inflation-rates", status_code=status.HTTP_200_OK)
def infaltion_rate_display(db: SessionDependency, current_user: CurrentUser):
    now = date.today()

    if current_user.Id:
        pir = calculate_pir_for_user(current_user.Id, now, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user does not exists (dashboard)."
        )
    return {
        "personal_inflation_rate": pir,
        "national_inflation_rate": 3.1,  # hardcode or fetch from SingStat (the CPI)
    }

@router.get("/calculate-pir")
def get_user_tornqvist_pir(db: SessionDependency, current_user: CurrentUser):
    if current_user.Id:
        # 1. Get Current Month Shares (from ExpensesDB)
        current_totals = get_monthly_category_totals(db, current_user.Id, date.today())
        current_shares = calculate_shares(current_totals)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user does not exists (dashboard)."
        )
    
    # 2. Get Base Month Shares (from PreviousExpenseDB)
    # Let's say we compare against the same month last year
    base_month_str = (date.today().replace(year=date.today().year - 1)).strftime("%Y-%m")
    
    base_record = db.exec(
        select(PreviousExpenseDB)
        .where(PreviousExpenseDB.UserId == current_user.Id)
        .where(PreviousExpenseDB.Month == base_month_str)
    ).first()
    
    if not base_record:
        # Fallback: if no data from 1 year ago, use the oldest available month
        base_record = db.exec(
            select(PreviousExpenseDB)
            .where(PreviousExpenseDB.UserId == current_user.Id)
            .order_by(PreviousExpenseDB.Month.asc())
        ).first()

    # Convert the DB model to a dict for the calculator
    base_totals = {
        "Food": base_record.Food,
        "Transport": base_record.Transport,
        "Utilities": base_record.Utilities,
        "Entertainment": base_record.Entertainment,
        "Shopping": base_record.Shopping,
        "Healthcare": base_record.Healthcare
    } if base_record else {}
    
    base_shares = calculate_shares(base_totals)

    # 3. Fetch Price Ratios from SingStat (Mocked for now)
    # In production, this comes from your API service
    mock_price_ratios = {
        "Food": 1.045,  # +4.5%
        "Transport": 1.02,
        "Utilities": 1.08,
        "Entertainment": 1.01,
        "Shopping": 1.03,
        "Healthcare": 1.05
    }

    # 4. Calculate final PIR
    pir_value = compute_tornqvist_pir(base_shares, current_shares, mock_price_ratios)
    
    return {
        "user_pir": pir_value,
        "comparison_month": base_month_str if base_record else "earliest_available"
    }

# 6-month forecast 
@router.get("/forecast", status_code=status.HTTP_200_OK)
def six_month_forecast_graph(session: SessionDependency, current_user: CurrentUser):
    now = date.today()

    # ── Build monthly spending history ──────────────────────────────────────
    # Step 1: pull from previous_expenses (imported history)
    prev_rows = session.exec(
        select(PreviousExpenseDB)
        .where(PreviousExpenseDB.UserId == current_user.Id)
        .order_by(PreviousExpenseDB.Month)
    ).all()

    # Each row has Food + Transport + ... → sum all categories
    history: dict[str, float] = {
        row.Month: row.Food + row.Transport + row.Utilities +
                   row.Entertainment + row.Shopping + row.Healthcare
        for row in prev_rows
    }

    # Step 2: fill in months from user_expenses (what they've logged in the app)
    # Go back up to 6 months
    for i in range(6, 0, -1):
        target = (now.replace(day=1) - timedelta(days=1))  # last day of prev month
        for _ in range(i - 1):
            target = (target.replace(day=1) - timedelta(days=1))
        target = target.replace(day=1)

        month_key = target.strftime("%Y-%m")
        if month_key in history:
            continue  # already have it from previous_expenses

        expenses = session.exec(
            select(ExpensesDB).where(
                ExpensesDB.UserId == current_user.Id,
                extract("month", ExpensesDB.DatePurchased) == target.month,
                extract("year", ExpensesDB.DatePurchased) == target.year,
            )
        ).all()
        if expenses:
            history[month_key] = sum(e.AmountSpent for e in expenses)

    # Sort by month and extract just the values
    sorted_spending = [v for _, v in sorted(history.items())]

    if len(sorted_spending) < 3:
        # Not enough data yet — return flat line based on whatever we have
        avg = sum(sorted_spending) / len(sorted_spending) if sorted_spending else 0
        sorted_spending = [avg] * 3

    # ── Fetch PIR to use as monthly inflation rate ───────────────────────────
    if current_user.Id:
        pir = calculate_pir_for_user(current_user.Id, now, session)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user does not exists (dashboard)."
        )
    monthly_rate = (pir / 100) / 12  # convert annual % → monthly decimal

    forecast_values = calculate_forecast(
        monthly_spending                 = sorted_spending,
        projected_monthly_inflation_rate = monthly_rate,
        months_ahead                     = 6,
    )

    # Build labels: next 6 months
    labels = [
        (now.replace(day=1) + timedelta(days=32 * i)).strftime("%b")
        for i in range(1, 7)
    ]

    return {"labels": labels, "data": forecast_values}

# spending breakdown
@router.get("/spending-breakdown", status_code=status.HTTP_200_OK)
def spending_breakdown(current_user: CurrentUser, session: SessionDependency):
    now = date.today()
    expenses = session.exec(
        select(ExpensesDB).where(
            ExpensesDB.UserId == current_user.Id,
            extract("month", ExpensesDB.DatePurchased) == now.month,
            extract("year", ExpensesDB.DatePurchased) == now.year,
        )
    ).all()

    breakdown: dict[str, float] = {}
    for e in expenses:
        breakdown[e.Type] = breakdown.get(e.Type, 0) + e.AmountSpent

    categories = ["food", "transport", "utilities", "entertainment", "shopping", "healthcare"]
    return {
        "labels": categories,
        "data":   [round(breakdown.get(c, 0), 2) for c in categories],
    }

# monthly trend: spending vs budget 
@router.get("/trend")
def get_monthly_trend(current_user: CurrentUser, session: SessionDependency):
    now   = date.today()
    budget = session.exec(select(UserBudgetDB).where(UserBudgetDB.UserId == current_user.Id)).first()
    monthly_budget = budget.TotalBudget if budget else 0

    results = []
    for i in range(2, -1, -1):  # 3 months ago → current
        # Walk back i months
        target = now.replace(day=1)
        for _ in range(i):
            target = (target - timedelta(days=1)).replace(day=1)

        expenses = session.exec(
            select(ExpensesDB).where(
                ExpensesDB.UserId == current_user.Id,
                extract("month", ExpensesDB.DatePurchased) == target.month,
                extract("year", ExpensesDB.DatePurchased) == target.year,
            )
        ).all()

        results.append({
            "month":  target.strftime("%b"),
            "actual": round(sum(e.AmountSpent for e in expenses), 2),
            "budget": monthly_budget,
        })

    return results
