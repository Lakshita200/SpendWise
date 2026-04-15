from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select
from ..utils.utils import update_monthly_totals
from ..database import SessionDependency
from ..models import BasketDB, DeleteBasketExpenses, UserDetails, UserExpensesBase
from ..oauth2 import get_current_active_user


router = APIRouter(prefix="/basket", tags=["Basket"])

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]

def search_for_similar(product_name: str, db: Session, user_id: int):
    # The '%' are wildcards. 
    # Example: 'egg' becomes '%egg%' which matches 'Grade A eggs' or 'eggplant'
    search_term = f"%{product_name}%"
    
    statement = (
        select(BasketDB)
        .where(col(BasketDB.UserId) == user_id)
        .where(col(BasketDB.ItemName).ilike(search_term)) 
    )

# add a item to the monthly basket
@router.post("/", response_model=BasketDB, status_code=status.HTTP_201_CREATED)
def add_basket_expense(expense: UserExpensesBase, db: SessionDependency, current_user: CurrentUser):

    if current_user.Id is None:
        raise HTTPException(status_code=400, detail="User ID not found")
    
    # Create DB object (Note: UserExpensesBase used as input schema)
    db_expense = BasketDB.model_validate(expense, update={"UserId": current_user.Id})
    
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # Refresh totals for the current month
    update_monthly_totals(db, current_user.Id, None, BasketDB)

    return db_expense

# delete a item to the monthly basket
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_basket_expense(delete_data: DeleteBasketExpenses, db: SessionDependency, current_user: CurrentUser):
    if current_user.Id is None:
        raise HTTPException(status_code=400, detail="User ID not found")
    
    # 1. Fetch only items belonging to this user from the ID list
    statement = select(BasketDB).where(
        col(BasketDB.Id).in_(delete_data.BasketExpensesId),
        BasketDB.UserId == current_user.Id
    )
    items = db.exec(statement).all()

    if not items:
        raise HTTPException(status_code=404, detail="No matching items found")

    # 2. Delete and Commit
    for item in items:
        db.delete(item)
    
    db.commit()

    # 3. Recalculate totals for the current month
    update_monthly_totals(db, current_user.Id, None, BasketDB)

    return None

# get a item to the monthly basket
router.get("/", response_model=list[BasketDB])
def get_basket_expenses(db: SessionDependency, current_user: CurrentUser):
    if current_user.Id is None:
            raise HTTPException(status_code=400, detail="User ID not found")

    statement = select(BasketDB).where(BasketDB.UserId == current_user.Id)
    return db.exec(statement).all()
