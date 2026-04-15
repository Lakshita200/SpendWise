from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, delete , or_, and_
from ..database import SessionDependency
from ..models import AlertBase, AlertDB, UserDetails
from ..oauth2 import get_current_active_user
from typing import Annotated
from datetime import datetime, timedelta, timezone


router = APIRouter(
    prefix="/dashboard", 
    tags=["dashboard"]
    )

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]

# gets all the alerts for the user 
@router.get("/", response_model=list[AlertBase])
def get_alerts(current_user: CurrentUser, db: SessionDependency):

    user_id = current_user.Id
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    return db.exec(
        select(AlertDB)
        .where(AlertDB.UserId == current_user.Id)
        .order_by(AlertDB.CreatedAt.desc())
    ).all()

# updates a alert in the database to read if the user has read it 
@router.put("/{alert_id}/read")
def mark_alert_as_read(alert_id: int,current_user: CurrentUser,db: SessionDependency):
    alert = db.get(AlertDB, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.UserId != current_user.Id:
        raise HTTPException(status_code=403, detail="Not allowed to modify this alert")

    alert.IsRead = True
    alert.ReadAt = datetime.now(timezone.utc)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert







