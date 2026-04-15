from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel import Session, select, func
from ..background import budget_warning_alert_generation
from ..utils.utils import update_monthly_totals
from ..models import MonthlyCategoryDB, UserExpenses, ExpensesDB, UserDetails
from ..database import SessionDependency
from ..oauth2 import get_current_active_user
from typing import Annotated
from datetime import date, timedelta

router = APIRouter(prefix="/expenses", tags=["Expenses"])

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]


# quick expenses?
@router.get("/", response_model=ExpensesDB, status_code=status.HTTP_200_OK)
def get_quick_expense(expense: UserExpenses, db: SessionDependency, current_user: CurrentUser):
    pass

# add expenses for any type to be saved in the db
@router.post("/", response_model=UserExpenses, status_code=status.HTTP_201_CREATED)
def add_expense(expense: UserExpenses, db: SessionDependency, current_user: CurrentUser, background_tasks: BackgroundTasks,):

    if current_user.Id is None:
        raise HTTPException(status_code=400, detail="User ID not found")
    
    """ db_expense = expense.model_dump()

    if db_expense["Recurring"]: """
        

    db_expense = ExpensesDB(**expense.model_dump(), UserId = current_user.Id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # add each category expenses 
    update_monthly_totals(db, current_user.Id, db_expense.DatePurchased, ExpensesDB)
    # checks if budget threshold ahs been exceeded eveytime a new expense is added 
    background_tasks.add_task(budget_warning_alert_generation, current_user.Id)

    return db_expense
