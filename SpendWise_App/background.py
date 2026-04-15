import asyncio
from datetime import datetime
import logging
from typing import Optional
from sqlmodel import Session, select
from .database import engine 
from .models import UserDetails, UserSettingsDB, UserBudgetDB, MonthlyCategoryDB, AlertDB



logger = logging.getLogger(__name__)

# creates the alert and stores it 
async def create_db_alert(user_id: int, title: str, message: str, alert_type: str):
    with Session(engine) as session:
        new_alert = AlertDB(
            UserId=user_id,
            Title=title,
            Message=message,
            AlertType=alert_type,  # use enum?
            IsRead=False
        )
        session.add(new_alert)
        session.commit()
    logger.debug(f"Generated {alert_type} alert for User ID: {user_id}")

# checks if user has exceeded budget threshold when a new expense is added 
# is called everytime the user adds a new expense
async def budget_warning_alert_generation(user_id: int):

    current_month = datetime.now().strftime("%Y-%m")

    with Session(engine) as session:
        # 1. Get User Settings
        settings = session.exec(
            select(UserSettingsDB).where(UserSettingsDB.UserId == user_id)
        ).first()

        # Exit if alerts are disabled or settings don't exist
        if not settings or not settings.BudgetThresholdAlerts:
            return

        # 2. Get User Budget
        budget = session.exec(
            select(UserBudgetDB).where(UserBudgetDB.UserId == user_id)
        ).first()

        # 3. Get Current Month's Spending
        spending = session.exec(
            select(MonthlyCategoryDB)
            .where(MonthlyCategoryDB.UserId == user_id)
            .where(MonthlyCategoryDB.Month == current_month)
        ).first()

        # Validation Check
        if not budget or not spending or budget.TotalBudget <= 0:
            return

        # 4. Calculate Total Spent (Summing all your category fields)
        total_spent = (
            spending.Food + 
            spending.Transport + 
            spending.Utilities +
            spending.Entertainment + 
            spending.Shopping + 
            spending.Healthcare + 
            spending.Other
        )

        # 5. Math: (Actual / Budget) vs (Threshold / 100)
        usage_ratio = total_spent / budget.TotalBudget
        # Fallback to 80% if no specific threshold is set
        threshold_ratio = (settings.BudgetThreshold or 80) / 100

        # 6. Condition Check
        if usage_ratio >= threshold_ratio:
            # We use create_task so we don't block this session's closure
            asyncio.create_task(
                create_db_alert(
                    user_id=user_id,
                    title="Budget Warning ⚠️",
                    message=f"You've spent ${total_spent:.2f}, reaching {usage_ratio:.0%} of your monthly budget.",
                    alert_type="budget"
                )
            )