# code for the math calc logics 

import math 
from datetime import date, timedelta
import calendar
from sqlmodel import Session, func, select

# 1. REAL-TIME SAVINGS (Pro-rated)
#Formula: Current Savings = (Monthly Income × (Days Passed / Total Days in Month))− Current Total Spending
def calculate_realtime_savings(
    monthly_income: float,
    current_total_spending: float,
    reference_date: date | None = None # optional or nah?
) -> float:

    if reference_date is None:
        reference_date = date.today()

    days_passed = reference_date.day
    total_days_in_month = calendar.monthrange(reference_date.year, reference_date.month)[1]

    prorated_income = monthly_income * (days_passed / total_days_in_month)
    savings = prorated_income - current_total_spending

    return round(savings, 2)




#-------------------------------------------------------------------------------------------------------------------------
# calculate tornqvist pir, all helpers and code 

# Converts absolute spending totals into percentage shares (0.0 to 1.0).
def calculate_shares(totals: dict[str, float]) -> dict[str, float]:
    total_spend = sum(totals.values())
    if total_spend == 0:
        return {}
    return {cat: amt / total_spend for cat, amt in totals.items()}

def compute_tornqvist_pir(base_shares: dict[str, float], current_shares: dict[str, float], price_ratios: dict[str, float]) -> float:
    """
    base_shares: { 'Food': 0.25, ... } (from MonthlyCategoryDB)
    current_shares: { 'Food': 0.30, ... } (from BasketCAtegoryDB)
    price_ratios: { 'Food': 1.03, ... } (from SingStat API)
    """
    log_sum = 0.0
    
    # We iterate over categories present in the price dataset
    for category, ratio in price_ratios.items():
        # Get shares, default to 0 if user didn't spend in that category
        s0 = base_shares.get(category, 0.0)
        st = current_shares.get(category, 0.0)
        
        # Törnqvist logic: Average share * natural log of price change
        if ratio > 0: # Avoid log(0)
            avg_share = (s0 + st) / 2
            log_sum += avg_share * math.log(ratio)
            
    # Convert back from log space to percentage
    pir = (math.exp(log_sum) - 1) * 100
    return round(pir, 2)
















# returns users personal inflation rate based on their spending 
def calculate_pir(items: list[dict]) -> float:
    """
    Each item in `items` should be a dict with:
        - 'name'         : str
        - 'base_price'   : float  (P0 - price in base period)
        - 'current_price': float  (Pt - price in current period)
        - 'weight'       : float  (wi - spending weight, e.g. monthly spend on item)

    Returns PIR as a percentage (e.g. 3.5 means 3.5% inflation).
    """
    numerator   = sum(item['current_price'] * item['weight'] for item in items)
    denominator = sum(item['base_price']    * item['weight'] for item in items)

    if denominator == 0:
        raise ValueError("Sum of (base_price × weight) cannot be zero.")

    pir = (numerator / denominator - 1) * 100 # -1 finds the change 
    return round(pir, 4)

# returns the inflated cost of living for each subsequent month based on PIR?
# can use PIR *IF* the PIR is calculated on a monthly basis
def calculate_forecast(
    monthly_spending: list[float],
    projected_monthly_inflation_rate: float, # when calling must PIR/100 because of how PIR is returned
    months_ahead: int = 6,
    ams_window: int = 3 # allows for variation of window
) -> list[float]:
    """
    Forecasts spending for the next `months_ahead` months.

    Steps:
        1. AMS = average of the last 3 months of spending
        2. En  = AMS × (1 + r)^n  for n = 1, 2, ..., months_ahead

    Args:
        monthly_spending              : list of historical monthly spending values
                                        (must have at least 3 entries)
        projected_monthly_inflation_rate : e.g. 0.005 for 0.5% per month
        months_ahead                  : how many months to forecast (default 6)

    """
    if len(monthly_spending) < ams_window:
        raise ValueError(f"Need at least {ams_window} months of spending history to forecast.")

    ams = sum(monthly_spending[-ams_window:]) / ams_window  # uses last `ams_window` months
    r   = projected_monthly_inflation_rate

    # forecast -->  Each index in the list corresponds to a future month
    forecast = [
        round(ams * (1 + r) ** n, 2)
        for n in range(1, months_ahead + 1)
    ]
    return forecast















#-------------------------------------------------------------------------------------------------------------------------
# Budget page calculations code 
def compute_budget_data(user_id: int, session: Session) -> dict:
    from SpendWise_App.models import ExpensesDB, PreviousExpenseDB

    today = date.today()
    first_of_current = today.replace(day=1)
    first_of_3_months_ago = (first_of_current - timedelta(days=3 * 28)).replace(day=1)

    categories = ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]

    # Get the 3 month keys we need
    months_needed = set()
    for i in range(1, 4):
        d = (first_of_current - timedelta(days=i * 28)).replace(day=1)
        months_needed.add(d.strftime("%Y-%m"))

    # ── 1. Query ExpensesDB (day-to-day expenses) ──
    expense_records = session.exec(
        select(ExpensesDB).where(
            ExpensesDB.UserId == user_id,
            ExpensesDB.DatePurchased >= first_of_3_months_ago,
            ExpensesDB.DatePurchased < first_of_current
        )
    ).all()

    # Group day-to-day expenses by month and category
    expense_by_month = {}
    for r in expense_records:
        month_key = r.DatePurchased.strftime("%Y-%m")
        if month_key not in expense_by_month:
            expense_by_month[month_key] = {cat: 0.0 for cat in categories}
        expense_type = r.Type
        if expense_type == "Food & Dining":
            expense_type = "Food"
        if expense_type in expense_by_month[month_key]:
            expense_by_month[month_key][expense_type] += r.AmountSpent

    # ── 2. Query PreviousExpenseDB and combine with day-to-day ──
    previous_records = session.exec(
        select(PreviousExpenseDB).where(
            PreviousExpenseDB.UserId == user_id,
            PreviousExpenseDB.Month.in_(months_needed)
        )
    ).all()

    for r in previous_records:
        if r.Month not in expense_by_month:
            expense_by_month[r.Month] = {cat: 0.0 for cat in categories}
        expense_by_month[r.Month]["Food"]          += r.Food
        expense_by_month[r.Month]["Transport"]     += r.Transport
        expense_by_month[r.Month]["Utilities"]     += r.Utilities
        expense_by_month[r.Month]["Entertainment"] += r.Entertainment
        expense_by_month[r.Month]["Shopping"]      += r.Shopping
        expense_by_month[r.Month]["Healthcare"]    += r.Healthcare

    # ── 3. Calculate averages ──
    if not expense_by_month:
        return {
            "auto_total": 0.0,
            "category_avgs": {cat: 0 for cat in categories},
            "category_proportions": {cat: round(1 / len(categories), 4) for cat in categories}
        }

    n = len(expense_by_month)
    cat_avgs = {
        cat: round(sum(expense_by_month[m][cat] for m in expense_by_month) / n, 2)
        for cat in categories
    }
    auto_total = round(sum(cat_avgs.values()), 2)

    # ── 4. Proportions ──
    if auto_total > 0:
        proportions = {cat: round(cat_avgs[cat] / auto_total, 4) for cat in categories}
    else:
        proportions = {cat: round(1 / len(categories), 4) for cat in categories}

    return {
        "auto_total": auto_total,
        "category_avgs": cat_avgs,
        "category_proportions": proportions
    }

# Keep as wrappers so nothing else breaks
def compute_auto_budget(user_id: int, session: Session) -> float:
    return compute_budget_data(user_id, session)["auto_total"]

def compute_category_budgets(user_id: int, session: Session) -> dict:
    return compute_budget_data(user_id, session)["category_avgs"]
# def compute_auto_budget(user_id: int, session: Session) -> float:
#     """
#     Auto Budget = average of the last 3 months' total spending.
#     Pulls directly from MonthlyCategoryDB which already tracks monthly totals.
#     """
#     from SpendWise_App.models import MonthlyCategoryDB  # local to avoid circular import

#     today = date.today()
#     months = []
#     for i in range(1, 4):  # last 3 months
#         d = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
#         months.append(d.strftime("%Y-%m"))

#     records = session.exec(
#         select(MonthlyCategoryDB).where(
#             MonthlyCategoryDB.UserId == user_id,
#             MonthlyCategoryDB.Month.in_(months)
#         )
#     ).all()

#     if not records:
#         return 0.0

#     totals = [
#         float(r.Food + r.Transport + r.Utilities + r.Entertainment + r.Shopping + r.Healthcare + r.Other)
#         for r in records
#     ]
#     return round(sum(totals) / len(totals), 2)

# def compute_category_budgets(user_id: int, session: Session) -> dict:
#     """
#     Returns avg of last 3 months spending per category.
#     If no history exists for a category, defaults to 0.
#     """
#     from SpendWise_App.models import MonthlyCategoryDB

#     today = date.today()
#     months = []
#     for i in range(1, 4):
#         d = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
#         months.append(d.strftime("%Y-%m"))

#     records = session.exec(
#         select(MonthlyCategoryDB).where(
#             MonthlyCategoryDB.UserId == user_id,
#             MonthlyCategoryDB.Month.in_(months)
#         )
#     ).all()

#     if not records:
#         return {
#             "Food": 0, "Transport": 0, "Utilities": 0,
#             "Entertainment": 0, "Shopping": 0, "Healthcare": 0, "Other": 0
#         }

#     n = len(records)
#     return {
#         "Food":          round(sum(r.Food          for r in records) / n, 2),
#         "Transport":     round(sum(r.Transport     for r in records) / n, 2),
#         "Utilities":     round(sum(r.Utilities     for r in records) / n, 2),
#         "Entertainment": round(sum(r.Entertainment for r in records) / n, 2),
#         "Shopping":      round(sum(r.Shopping      for r in records) / n, 2),
#         "Healthcare":    round(sum(r.Healthcare    for r in records) / n, 2),
#         "Other":         round(sum(r.Other         for r in records) / n, 2),
#     }

# def distribute_budget(blank_vals: dict, remaining_budget: float) -> dict:
#     """
#     Iteratively reduces blank category budgets until their total 
#     fits within remaining_budget, flooring at 0 per category.
#     """
#     cats = {k: round(float(v), 2) for k, v in blank_vals.items()}

#     while True:
#         total = sum(cats.values())
#         if total <= remaining_budget:
#             break

#         active_cats = {k: v for k, v in cats.items() if v > 0}
#         if not active_cats:
#             break

#         excess = total - remaining_budget
#         reduction = excess / len(active_cats)

#         for cat in active_cats:
#             cats[cat] = max(0, round(cats[cat] - reduction, 2))

#     return cats


def build_budget_suggestions(user_id: int, session: Session) -> list[dict]:
    from SpendWise_App.models import MonthlyCategoryDB

    month_str = date.today().strftime("%Y-%m")
    record = session.exec(
        select(MonthlyCategoryDB).where(
            MonthlyCategoryDB.UserId == user_id,
            MonthlyCategoryDB.Month == month_str
        )
    ).first()

    if not record:
        return []

    suggestions = []

    # ── Food ─────────────────────────────────────────────────
    # Singapore avg: $500-700 eating out, $200-300 cooking at home
    if record.Food > 600:
        suggestions.append({
            "title": "Reduce Dining Out",
            "description": (
                f"You've spent ${record.Food:,.0f} on food this month. "
                "Singaporeans who meal prep or cook at home spend 40% less — "
                "try hawker centres over restaurants to save more."
            ),
            "savings": round(record.Food * 0.30, 2),
        })

    # ── Transport ─────────────────────────────────────────────
    # Singapore avg: $100-150 public transport, $500-1000 Grab daily
    if record.Transport > 250:
        suggestions.append({
            "title": "Switch to Public Transport",
            "description": (
                f"You've spent ${record.Transport:,.0f} on transport this month. "
                "Taking MRT/bus instead of Grab 3 days a week could cut your "
                "transport costs significantly — avg MRT fare is just $1.60 per trip."
            ),
            "savings": round(record.Transport * 0.35, 2),
        })

    # ── Utilities ─────────────────────────────────────────────
    # Singapore avg: $140-300 for small apartment
    if record.Utilities > 300:
        suggestions.append({
            "title": "Reduce Utility Usage",
            "description": (
                f"You've spent ${record.Utilities:,.0f} on utilities this month, "
                "above the Singapore average of $140-300. "
                "Setting your aircon to 25°C and using off-peak hours can reduce bills by 20%."
            ),
            "savings": round(record.Utilities * 0.20, 2),
        })

    # ── Entertainment ─────────────────────────────────────────
    # Singapore avg: $200-400/month
    if record.Entertainment > 400:
        suggestions.append({
            "title": "Review Entertainment Subscriptions",
            "description": (
                f"You've spent ${record.Entertainment:,.0f} on entertainment this month. "
                "Check for unused subscriptions — Singapore's free alternatives like "
                "NLB libraries, parks, and community events can replace paid activities."
            ),
            "savings": round(record.Entertainment * 0.25, 2),
        })

    # ── Shopping ──────────────────────────────────────────────
    # Singapore avg: $200-400/month
    if record.Shopping > 500:
        suggestions.append({
            "title": "Cut Back on Shopping",
            "description": (
                f"You've spent ${record.Shopping:,.0f} on shopping this month. "
                "Try the 48-hour rule — wait 2 days before non-essential purchases. "
                "Shopee and Carousell also offer cheaper alternatives to retail prices."
            ),
            "savings": round(record.Shopping * 0.30, 2),
        })

    # ── Healthcare ────────────────────────────────────────────
    # Singapore avg: ~$200/month, polyclinic visits ~$15 vs private ~$80+
    if record.Healthcare > 200:
        suggestions.append({
            "title": "Use Polyclinics Over Private Clinics",
            "description": (
                f"You've spent ${record.Healthcare:,.0f} on healthcare this month. "
                "Polyclinic visits cost as little as $15 vs $80+ at private clinics "
                "for the same treatment. Check if your MediShield Life covers recent bills."
            ),
            "savings": round(record.Healthcare * 0.25, 2),
        })

    # ── Other ─────────────────────────────────────────────────
    if record.Other > 300:
        suggestions.append({
            "title": "Review Miscellaneous Spending",
            "description": (
                f"You've spent ${record.Other:,.0f} on miscellaneous items this month. "
                "Tracking these smaller expenses can reveal hidden spending patterns "
                "that add up over time."
            ),
            "savings": round(record.Other * 0.20, 2),
        })

    return suggestions






