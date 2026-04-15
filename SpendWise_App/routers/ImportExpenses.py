from sqlalchemy.exc import SQLAlchemyError
from fastapi import status, HTTPException, Depends, APIRouter, Query
from sqlmodel import col, delete
from .settings import create_default_settings
from ..oauth2 import get_current_active_user
from ..models import *
from ..database import *


router = APIRouter(
    prefix="/import",
    tags=['Import Past Expenses']
)

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]


# for importing previous expenses and saving to db
@router.put("/previous-expenses", response_model=list[PreviousExpenseDB])
def save_previous_expenses(current_user: CurrentUser, payload: list[PreviousExpense], db: SessionDependency):
    
    user_id = current_user.Id
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    settings = db.exec(select(UserSettingsDB).where(UserSettingsDB.UserId == user_id)).first()
    if not settings:
        settings = create_default_settings(db, user_id)

    try:
        # 1. Identify which months are in the incoming payload
        # (Assuming row_data has a .Month attribute like "January" or a date object)
        incoming_months = {row.Month for row in payload} 

        # 2. Check if ANY of those months already exist in the DB for this user
        existing_records = db.exec(
            select(PreviousExpenseDB).where(
                PreviousExpenseDB.UserId == user_id,
                PreviousExpenseDB.Month.in_(incoming_months)
            )
        ).first()

        if existing_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data already exists for one or more of the provided months ({existing_records.Month})."
            )

        # 3. If no conflicts, proceed to save (Remove the delete statement!)
        new_rows = []
        for row_data in payload:
            record = PreviousExpenseDB(
                UserId=user_id,
                **row_data.model_dump()
            )
            db.add(record)
            new_rows.append(record)

        db.commit()
        # ... refresh and return ...

        for row in new_rows:
            db.refresh(row)

        return new_rows

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save previous expenses."
        )

# to display all previous expenses with filters using querys (/101/previous-expenses?page=1&year=2026)
@router.get("/previous-expenses", response_model=list[PreviousExpenseDB])
def get_previous_expenses(
    current_user: CurrentUser,
    db: SessionDependency,
    year: int | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(6, ge=1, le=100)
):
    statement = select(PreviousExpenseDB).where(
        PreviousExpenseDB.UserId == current_user.Id
    )
    if year:
        statement = statement.where(PreviousExpenseDB.Month.startswith(f"{year}-"))
    
    offset_value = (page - 1) * size
    statement = statement.order_by(
        col(PreviousExpenseDB.Month).desc()
    ).offset(offset_value).limit(size)

    results = db.exec(statement).all()

    if not results and page == 1:
        raise HTTPException(status_code=404, detail="No expenses found.")

    return results


# delete selected expenses based on display (takes in all the expense ids)
@router.delete("/{user_id}/previous-expenses/delete")
def delete_multiple_expenses(user_id: int, payload: DeleteExpensesRequest, db: SessionDependency):
    if not payload.expenses_ids:
        raise HTTPException(status_code=400, detail="No IDs provided.")

    try:
        # Wrapping in col() tells VS Code these are DB columns
        statement = delete(PreviousExpenseDB).where(
            col(PreviousExpenseDB.Id).in_(payload.expenses_ids),
            col(PreviousExpenseDB.UserId) == user_id
)
        
        result = db.exec(statement)
        db.commit()

        return {
            "success": True, 
            "deleted_count": result.rowcount
        }

    except SQLAlchemyError:
        db.rollback()
        # print(f"Error: {e}") # It's helpful to log the error during development
        raise HTTPException(
            status_code=500, 
            detail="Bulk deletion failed."
        )
