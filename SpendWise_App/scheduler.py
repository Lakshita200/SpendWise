# code that will be called by the scheduler 

import asyncio
import logging
from fastapi import HTTPException
from sqlmodel import Session, delete, or_, select
from .database import engine  # Import your SQLAlchemy/SQLModel engine
from datetime import datetime, timedelta, timezone
from .models import BasketCategoryDB, UserDetails, UserSettingsDB, UserBudgetDB, MonthlyCategoryDB, AlertDB



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

# add all the functions that are called inside 
async def all_scheduler_calls():

    pass 

# pulls the online data into the database
async def get_online_data():
    pass

# checks if a basket item's price has increase pass their set threshold 
# is called everytime when??
async def price_increase_alert():
    # Only checks users who have are online
    statement = select(UserDetails).where(UserDetails.RefreshToken != None)
    
    with Session(engine) as session:
        available_users = session.exec(statement).all()
        
        for user in available_users:
            user_id = user.Id
            basket_statement = select(BasketCategoryDB).where(BasketCategoryDB.UserId == user_id)
            settings_statement = select(UserSettingsDB).where(UserSettingsDB.UserId == user_id)

            settings = session.exec(settings_statement).one()
            basket = session.exec(basket_statement).one()
            if not settings or not settings.PriceIncreaseAlerts:
                logger.debug(f"User {user.Id} settings skip")
                continue
            elif not basket:
                logger.debug(f"User {user.Id} basket skip")
                continue

            #-------------------------------------------------
            # math and check logic
            #-------------------------------------------------     
            
            if True: #add condition if necessary
                # We use create_task so we don't block this session's closure
                asyncio.create_task(
                    create_db_alert(
                        user_id=user_id,
                        title="Price Increase ⚠️",
                        message=f"The price of the {db_category} category has increased by ${price_increase:.2f}",
                        alert_type="price_increase"
                    )
                )

# removes old alerts 
async def cleanup_old_alerts(unread_days: int = 30):
    unread_cutoff = datetime.now(timezone.utc) - timedelta(days=unread_days)

    # (Delete if IsRead is True) OR (Delete if CreatedAt is older than 30 days)
    statement = delete(AlertDB).where(
        or_(
            AlertDB.IsRead == True,
            AlertDB.CreatedAt < unread_cutoff
        )
    )

    with Session(engine) as session:
        try:
            session.exec(statement)
            session.commit()
            logger.info("Successfully cleaned up old alerts from the database.")
        except Exception as e:
            logger.error(f"Error during alert cleanup: {e}")
            session.rollback()



