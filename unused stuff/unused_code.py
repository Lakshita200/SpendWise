#CALCULATIONS.PY DEMO CODE 

# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────

# --- PIR Demo ---
basket = [
    {"name": "Rice (5kg)",    "base_price": 8.00,  "current_price": 8.80,  "weight": 40},
    {"name": "Transport",     "base_price": 90.00, "current_price": 95.00, "weight": 90},
    {"name": "Groceries",     "base_price": 200.0, "current_price": 215.0, "weight": 200},
    {"name": "Dining out",    "base_price": 150.0, "current_price": 160.0, "weight": 150},
]
pir = calculate_pir(basket)
print(f"Personal Inflation Rate : {pir:.2f}%")

# --- Forecast Demo ---
past_spending = [1800, 1950, 1870]           # last 3 months
monthly_inflation = 0.005                    # 0.5% per month
forecast = calculate_forecast(past_spending, monthly_inflation, months_ahead=6)
print("\n6-Month Spending Forecast:")
for i, amount in enumerate(forecast, 1):
    print(f"  Month {i}: ${amount:.2f}")


# class UserSettingsBase(SQLModel):
#     UserId: int = Field(foreign_key="user_details.id", unique=True, index=True)
#     EmailOrPhone: Optional[str] = None
#     MonthlyIncome: float = Field(default=0.0, ge=0)
#     HouseholdSize: int = Field(default=1, ge=1)
#     TransportationType: TransportationTypeEnum = Field(default(TransportationTypeEnum.public))
#     MonthlyTransportSpending: float = Field(default=0.0, ge=0)
#     MonthlyUtilityBill: float = Field(default=0.0, ge=0)
#     PriceIncreaseAlerts: bool = True
#     BudgetThresholdAlerts: bool = True
#     AlertThreshold: int = Field(default=80, ge=1, le=100)


class UserMonthly(SQLModel):
    income: int
    HouseholdSize: int
    TransportType: str
    TransportCost: int
    utilities: int 

class MonthlyDB(UserMonthly):
    __tablename__ = "user_Monthly" # type: ignore
    # user_id relationship column?
    id: int | None = Field(default=None, primary_key=True)
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

class UserAlerts(SQLModel):
    PriceIncrease: bool = False
    BudgetThreshold: bool = False
    AlertThreshold: int

class AlertsDB(UserAlerts):
    __tablename__ = "user_alerts" # type: ignore
    # user_id relationship column?
    id: int | None = Field(default=None, primary_key=True)
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

settings = UserSettingsDB(
        UserId=user_id,
        Email=email,
        MonthlyIncome=0.0,
        HouseholdSize=1,
        #TransportationType=TransportationEnum.public,
        TransportationType=TransportationTypeEnum.public,
        MonthlyTransportSpending=0.0,
        MonthlyUtilityBill=0.0,
        PriceIncreaseAlerts=True,
        BudgetThresholdAlerts=True,
        AlertThreshold=80,
    )


"""@router.get("/{user_id}/previous-expenses", response_model=List[PreviousExpenseResponse])
def get_previous_expenses(user_id: int, db: Session = Depends(get_db)):

    Load previous expenses table.

    settings = get_settings_by_user_id(db, user_id)
    if not settings:
        settings = create_default_settings(db, user_id)

    rows = (
        db.query(PreviousExpense)
        .filter(PreviousExpense.settings_id == settings.id)
        .order_by(PreviousExpense.month.desc())
        .all()
    )
    return rows"""

class UserSettingsUpdate(SQLModel):
    EmailOrPhone: Optional[str] = None
    MonthlyIncome: Optional[float] = Field(default=None, ge=0)
    HouseholdSize: Optional[int] = Field(default=None, ge=1)
    TransportationType: Optional[TransportationTypeEnum] = None
    MonthlyTransportSpending: Optional[float] = Field(default=None, ge=0)
    MonthlyUtilityBill: Optional[float] = Field(default=None, ge=0)
    PriceIncreaseAlerts: Optional[bool] = None
    BudgetThresholdAlerts: Optional[bool] = None
    AlertThreshold: Optional[int] = Field(default=None, ge=1, le=100)


#QUICK SETUP OPTION
@router.put("/{user_id}/quick-setup", response_model=UserSettingsRead)
def quick_setup(user_id: int, payload: QuickSetup, db: SessionDependency):
    settings = get_settings_by_user_id(db, user_id)
    if not settings:
        settings = create_default_settings(db, user_id)

    settings.MonthlyIncome = payload.MonthlyIncome
    if payload.Email is not None:
        settings.Email = payload.Email

    settings.SetupMode = "quick"
    settings.SetupCompleted = True

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings

class PreviousExpenseDB(PreviousExpense, table=True):
    __tablename__ = "previous_expenses" # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    #UserId: int = Field(foreign_key = "user_details.id")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )    
    SettingsId: int = Field(
        foreign_key="user_settings.id", 
        ondelete="CASCADE", 
        nullable=False, 
        index=True
    )
    
    Settings: Optional["UserSettingsDB"] = Relationship(back_populates="PreviousExpenses")

# for importing previous expenses and saving to db
@router.put("/{user_id}/previous-expenses", response_model=list[PreviousExpense]) # no need response model?
def save_previous_expenses(
    user_id: int,
    payload: AllPreviousExpenses,
    db: SessionDependency
):

    try:
        # Delete existing rows using SQLModel delete statement
        statement = delete(PreviousExpenseDB).where(PreviousExpenseDB.SettingsId == settings.id)
        db.exec(statement)

        new_rows = []
        for row_data in payload.AllExpenseRows:
            # Create new record using PascalCase fields
            record = PreviousExpenseDB(
                **row_data.model_dump(), SettingsId=settings.id 
            )
            db.add(record)
            new_rows.append(record)

        db.commit()
        
        for row in new_rows:
            db.refresh(row)

        return new_rows

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save previous expenses."
        )

# for deleting past expenses that were already saved into the db
@router.delete("/{user_id}/previous-expenses/{expense_id}")
def delete_previous_expense(user_id: int, expense_id: int, db: SessionDependency):
    # Verify settings exist first
    settings = get_settings_by_user_id(db, user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found.")

    # Find the specific row
    statement = select(PreviousExpenseDB).where(
        PreviousExpenseDB.id == expense_id,
        PreviousExpenseDB.SettingsId == settings.id 
    )
    expense = db.exec(statement).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense record not found.")

    try:
        db.delete(expense)
        db.commit()
        return {"success": True}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Deletion failed.")


#to update (save) a user’s settings in the database.
@router.put("/{user_id}", response_model=UserSettingsRead) 
def save_settings(user_id: int, payload: UserSettingsUpdate, db: SessionDependency):
    """Updates user settings fields."""
    settings = get_settings_by_user_id(db, user_id)
    if not settings:
        settings = create_default_settings(db, user_id)

    try:
         # check how frontend handles the data input?
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(settings, key, value)
        
        settings.UpdatedAt = datetime.utcnow() # change 

        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save settings."
        )

#QUICK SETUP OPTION
@router.put("/{user_id}/quick-setup", response_model=UserSettingsRead)
def quick_setup(user_id: int, payload: QuickSetupPayload, db: SessionDependency):
    settings = get_settings_by_user_id(db, user_id)
    if not settings:
        settings = create_default_settings(db, user_id)

    settings.MonthlyIncome = payload.MonthlyIncome
    if payload.EmailOrPhone is not None:
        settings.EmailOrPhone = payload.EmailOrPhone

    settings.SetupMode = "quick"
    settings.SetupCompleted = True
    settings.UpdatedAt = datetime.utcnow()

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings

#DETAILED SETUP OPTION
@router.put("/{user_id}/detailed-setup", response_model=UserSettingsRead)
def detailed_setup(user_id: int, payload: UserSettingsUpdate, db: SessionDependency):
    settings = get_settings_by_user_id(db, user_id)
    if not settings:
        settings = create_default_settings(db, user_id)

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(settings, key, value)

    settings.SetupMode = "detailed"
    settings.SetupCompleted = True
    settings.UpdatedAt = datetime.utcnow()

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings
    

class UserSettingsRead(SQLModel):
    id: int
    UserId: int
    EmailOrPhone: Optional[str]
    MonthlyIncome: float
    HouseholdSize: int
    TransportationType: TransportationTypeEnum
    MonthlyTransportSpending: float
    MonthlyUtilityBill: float
    PriceIncreaseAlerts: bool
    BudgetThresholdAlerts: bool
    AlertThreshold: int
    SetupMode: str
    SetupCompleted: bool
    CreatedAt: datetime
    UpdatedAt: datetime | None = None

# gets the settings of the user to be displaayed
@router.get("/{user_id}", response_model=UserSettings) 
def get_user_settings(user_id: int, db: SessionDependency):
    settings = get_settings_by_user_id(db, user_id)
    if not settings:
        settings = create_default_settings(db, user_id)
    return settings


def create_default_settings(db: Session, user_id: int) -> UserSettingsDB: #if not, create default settings for the user
    email = get_user_email(db, user_id)

    settings = UserSettingsDB(
        UserId=user_id,
        Email=email,
        # do not need to set default values
    )

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings
class FullSettingsResponse(UserSettingsRead):
    # Id: int
    # UserId: int
    # CreatedAt: datetime
    # UpdatedAt: datetime
    PreviousExpenses: list[PreviousExpense] = []


# add expenses for any type to be saved in the db
@router.post("/", response_model=ExpensesDB, status_code=status.HTTP_201_CREATED)
def add_expense(expense: UserExpenses, db: SessionDependency, current_user: CurrentUser):

    db_expense = ExpensesDB(**expense.model_dump(), user_id=current_user.id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense



def update_monthly_totals(db: Session, user_id: int, target_date: date | None, model: Type[Union[ExpensesDB, BasketDB]]):
    
    # --- BRANCH 1: BASKET LOGIC ---
    if target_date is None and model == BasketDB:
        query = (
            select(model.Type, func.sum(model.AmountSpent))
            .where(model.UserId == user_id)
            .group_by(model.Type)
        )
        results = db.exec(query).all()
        new_totals = {category: float(amount) for category, amount in results}
        
        # FIX: Ensure we use the correct variable name (basket_rec)
        basket_rec = db.exec(select(BasketCategoryDB).where(BasketCategoryDB.UserId == user_id)).first()
        
        if not basket_rec:
            basket_rec = BasketCategoryDB(  # FIX: was monthly_rec
                UserId=user_id,
                Food=0, Transport=0, Utilities=0, Entertainment=0, 
                Shopping=0, Healthcare=0, Other=0
            )
            db.add(basket_rec)

        for cat in ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]:
            setattr(basket_rec, cat, new_totals.get(cat, 0))

        db.commit()

    # --- BRANCH 2: EXPENSES LOGIC ---
    elif target_date is not None and model == ExpensesDB:
        month_str = target_date.strftime("%Y-%m")
    
        start_of_month = target_date.replace(day=1)
        if start_of_month.month == 12:
            next_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
        else:
            next_month = start_of_month.replace(month=start_of_month.month + 1)
            
        query = (
            select(model.Type, func.sum(model.AmountSpent))
            .where(model.UserId == user_id)
            .where(model.DatePurchased >= start_of_month)
            .where(model.DatePurchased < next_month)
            .group_by(model.Type)
        )
        results = db.exec(query).all()
        new_totals = {category: float(amount) for category, amount in results}
        
        # FIX: You must filter by BOTH UserId AND Month, otherwise you'll update the wrong month
        monthly_rec = db.exec(
            select(MonthlyCategoryDB)
            .where(MonthlyCategoryDB.UserId == user_id)
            .where(MonthlyCategoryDB.Month == month_str)
        ).first()
        
        if not monthly_rec:
            monthly_rec = MonthlyCategoryDB(
                UserId=user_id,
                Month=month_str,
                Food=0, Transport=0, Utilities=0, Entertainment=0, 
                Shopping=0, Healthcare=0, Other=0
            )
            db.add(monthly_rec)

        for cat in ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]:
            setattr(monthly_rec, cat, new_totals.get(cat, 0))

        db.commit()

# generate a alert and stores it inside the DB
@router.post("/", response_model=AlertDB)
def create_alert(payload: AlertCreate, current_user: CurrentUser, db: SessionDependency):
    
    user_id = current_user.Id
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    return create_alert_internal(
        db=db,
        user_id=user_id,
        title=payload.Title,
        message=payload.Message,
        alert_type=payload.AlertType
    )

# deletes a alert from the DB
@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: CurrentUser,
    db: SessionDependency
):
    alert = db.get(AlertDB, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.UserId != current_user.Id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this alert")

    db.delete(alert)
    db.commit()
    return {"success": True}



def create_alert_internal(db, user_id: int, title: str, message: str, alert_type: str):
    existing_alert = db.exec(
        select(AlertDB).where(
            AlertDB.UserId == user_id,
            AlertDB.Title == title,
            AlertDB.Message == message,
            AlertDB.Type == alert_type,
            AlertDB.IsRead == False
        )
    ).first()

    if existing_alert:
        return existing_alert

    alert = AlertDB(
        UserId=user_id,
        Title=title,
        Message=message,
        Type=alert_type,
        IsRead=False,
        CreatedAt=datetime.utcnow()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# old register route
# Register and send verification email
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register_user(user: UserCreate, db: SessionDependency):
    existing_user = get_user(db, email=user.Email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.Password)
    
    # Generate verification code
    verification_code = generate_verification_code()

    new_user = UserDetails(
        Email=user.Email,
        HashedPassword=hashed_pw,
        UserType="user",
        Active=False,  # User is inactive until email is verified
        EmailVerified=False,
        VerificationCode=verification_code,
        VerificationCodeExpiry=get_verification_code_expiry()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send verification email
    email_sent = send_verification_email(user.Email, verification_code)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )

    return new_user


# old setup codes 
""" # FOR QUICK SETUP, DETAILED SETUP AND FILL IN LATER OPTIONS

#FILL IN LATER OPTION
@router.post("/fill-later", response_model=UserSettingsDB)
def fill_in_later_setup(current_user: CurrentUser, db: SessionDependency):

    user_id = current_user.Id
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    settings = db.exec(select(UserSettingsDB).where(UserSettingsDB.UserId == user_id)).first()

    if not settings:
        settings = create_default_settings(db, user_id)

    settings.SetupMode = "skipped"
    settings.SetupCompleted = False

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings



#QUICK SETUP OPTION
@router.post("/quick-setup", response_model=UserSettingsDB)
def quick_setup(current_user: CurrentUser, payload: QuickSetup, db: SessionDependency):
    
    user_id = current_user.Id
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    settings = db.exec(select(UserSettingsDB).where(UserSettingsDB.UserId == user_id)).first()

    if not settings:
        settings = create_default_settings(db, user_id)

    settings.MonthlyIncome = payload.MonthlyIncome
    settings.SetupMode = "quick"
    settings.SetupCompleted = True

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


#DETAILED SETUP OPTION
@router.post("/detailed-setup", response_model=UserSettingsDB)
def detailed_setup(current_user: CurrentUser, payload: UserSettingsUpdate, db: SessionDependency):
    
    user_id = current_user.Id
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings = db.exec(select(UserSettingsDB).where(UserSettingsDB.UserId == user_id)).first()

    if not settings:
        settings = create_default_settings(db, user_id)

    ALLOWED_SETTINGS_FIELDS = {
    "MonthlyIncome",
    "HouseholdSize",
    "TransportationTypes",
    "MonthlyTransportSpending",
    "MonthlyUtilityBill",
    "PriceIncreaseAlerts",
    "BudgetThresholdAlerts",
    "AlertThreshold",
    "PriceThreshold",
    "BudgetThreshold",
}
    
    data = payload.model_dump(exclude_unset=True)

    for key, value in data.items():
        if key in ALLOWED_SETTINGS_FIELDS:
            setattr(settings, key, value)

    settings.SetupMode = "detailed"
    settings.SetupCompleted = True

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings """