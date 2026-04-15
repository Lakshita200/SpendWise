# code for models for database
# login schema not neccessary just use OAuth2PasswordRequestForm

from datetime import datetime, date 
from .enums import *
import re
from pydantic import AfterValidator, EmailStr, field_validator
from sqlalchemy import text
from sqlmodel import Field, Relationship, SQLModel, text, AutoString, Column, String, ARRAY
from typing import Annotated, Optional



""" # ENUMS
class TransportationType(str, Enum):
    default = "default"
    bus = "bus"
    Train = "train"
    bike = "bike"
    walking = "walking"
    electric = "electric"
    hybrid = "hybrid"
    gasoline = "gasoline"
    taxi = "taxi"
    privatehire = "privatehire"

    # private = "private" """

def validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(v) > 100:
        raise ValueError("Password has a maximum length of 100 characters")
    if not any(char.isdigit() for char in v):
        raise ValueError("Password must contain at least one number")
    if not any(char.isupper() for char in v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>+]", v):
        raise ValueError("Password must contain at least one special character")
    return v

StrongPassword = Annotated[str, AfterValidator(validate_password_strength)]

class UserBase(SQLModel):
    # index=True tells SQLModel to ask the database to create an index
    # makes lookups and filters on it faster.S
    Email: EmailStr = Field(unique=True, sa_type=AutoString, index=True) #auto string?????
    Active: bool | None = Field(default=True) # check if user is banned

class UserCreate(UserBase):
    Password: StrongPassword # plain password

class UserVerifyPassword(SQLModel):
    Password: str # plain password to compare to db pw

class UserChangePassword(UserVerifyPassword):
    RePassword: StrongPassword # re-enter the same pw

class UserDeleteAccount(UserVerifyPassword):
    IsSure: bool = False # ask user if they are sure they want to delete their account 
    DataDelete: bool = False # warn user all data will be deleted

class RefreshToken(SQLModel):
    RefreshToken: str | None = Field(default=None)

class UserDetails(UserBase, RefreshToken, table=True):
    __tablename__ = "user_details" # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    HashedPassword: str = Field(index=True)
    UserType: str = Field(default="user")
    EmailVerified: bool = Field(default=False)  # Email verification status
    VerificationCode: str | None = Field(default=None)  # Code sent to email
    VerificationCodeExpiry: datetime | None = Field(default=None)  # Expiry time for verification code
    ResetToken: str | None = Field(default=None)  # Token for password reset
    ResetTokenExpiry: datetime | None = Field(default=None)  # Expiry time for reset token
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    PreviousExpenses: list["PreviousExpenseDB"] = Relationship(back_populates="UserDetails", cascade_delete=True)
    AddedExpenses: list["ExpensesDB"] = Relationship(back_populates="UserDetails", cascade_delete=True)
    AddedBasket: list["BasketDB"] = Relationship(back_populates="UserDetails", cascade_delete=True)
    MonthlyTotal: list["MonthlyCategoryDB"] = Relationship(back_populates="UserDetails", cascade_delete=True)
    BasketTotal: "BasketCategoryDB" = Relationship(back_populates="UserDetails", cascade_delete=True)
    UserBudget: "UserBudgetDB" = Relationship(back_populates="UserDetails", cascade_delete=True)
    UserSettings: "UserSettingsDB" = Relationship(back_populates="UserDetails", cascade_delete=True)
    UserAlerts: list["AlertDB"] = Relationship(back_populates="UserDetails", cascade_delete=True)
    

# Avoid returning iportant data --> use id to fetch from db?
class UserResponse(UserBase):
    Id: int

class Token(RefreshToken):
    AccessToken: str
    TokenType: str
    UserType: str

class TokenData(SQLModel):
    Sub: str

# Email verification
class VerifyEmailRequest(SQLModel):
    Email: EmailStr
    VerificationCode: str

# Forgot password - request reset
class ForgotPasswordRequest(SQLModel):
    Email: EmailStr

# Forgot password - verify code and reset
class ResetPasswordRequest(SQLModel):
    Email: EmailStr
    ResetCode: str
    NewPassword: StrongPassword
    ReNewPassword: StrongPassword

    @field_validator("ReNewPassword")
    @classmethod
    def passwords_match(cls, v, info):
        if info.data.get("NewPassword") != v:
            raise ValueError("Passwords do not match")
        return v

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# expenses stuff
class UserExpensesBase(SQLModel): 
    Type: str # change to enum?
    ItemName: str 
    AmountSpent: float 
    Note: str | None = None

class UserExpenses(UserExpensesBase):
    # Recurring: bool = False
    DatePurchased: date # uses yyyy-mm-dd format

class ExpensesDB(UserExpenses, table=True):
    __tablename__ = "user_expenses" # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key = "user_details.Id", index=True, ondelete="CASCADE")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    UserDetails: "UserDetails" = Relationship(back_populates="AddedExpenses")

class BasketDB(UserExpensesBase, table=True):
    __tablename__ = "user_basket" # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key = "user_details.Id", index=True, ondelete="CASCADE")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    UserDetails: "UserDetails" = Relationship(back_populates="AddedBasket")

class DeleteBasketExpenses(SQLModel):
    BasketExpensesId: list[int]

class ExpensesByCategory(SQLModel):
    Food: int
    Transport: int
    Utilities: int
    Entertainment: int
    Shopping: int
    Healthcare: int
    Other: int

class MonthlyCategory(ExpensesByCategory):
    Month: str = Field(min_length=7, max_length=7, index=True, description="format: YYYY-MM")

    @field_validator("Month")
    @classmethod
    def validate_month(cls, value: str):
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise ValueError("Month must be in YYYY-MM format.")
        return value
    
class MonthlyCategoryDB(MonthlyCategory, table=True):
    __tablename__ = "monthly_category_total_spending" # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key = "user_details.Id", index=True, ondelete="CASCADE")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    UserDetails: "UserDetails" = Relationship(back_populates="MonthlyTotal")

class BasketCategoryDB(ExpensesByCategory, table=True):
    __tablename__ = "bakset_category_total_spending" # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key = "user_details.Id", index=True, ondelete="CASCADE")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    UserDetails: "UserDetails" = Relationship(back_populates="BasketTotal")

class ExpenseItem(SQLModel):
    Id: int
    ItemName: str
    AmountSpent: float
    DatePurchased: date
    Note: str | None = None
    Type: str

    class Config:
        from_attributes = True

class CategorySummary(SQLModel):
    category: str
    total: float
    expenses: list[ExpenseItem]



#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# for the budget page (add check to make sure addition makes sense? or do in method/route)
class UserBudget(ExpensesByCategory):
    TotalBudget: int
    AutoBudget: bool = True

class UserBudgetDB(UserBudget, table=True):
    __tablename__ = "user_budget" # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key = "user_details.Id", index=True, ondelete="CASCADE")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    UserDetails: "UserDetails" = Relationship(back_populates="UserBudget")

class CategoryBudgetInput(SQLModel):
    Food:          Optional[int] = Field(default=None, ge=0)
    Transport:     Optional[int] = Field(default=None, ge=0)
    Utilities:     Optional[int] = Field(default=None, ge=0)
    Entertainment: Optional[int] = Field(default=None, ge=0)
    Shopping:      Optional[int] = Field(default=None, ge=0)
    Healthcare:    Optional[int] = Field(default=None, ge=0)
    Other:         Optional[int] = Field(default=None, ge=0)

class BudgetSettingsRequest(SQLModel):
    AutoBudget:      bool
    TotalBudget:     Optional[int]              = Field(default=None, ge=0)
    CategoryBudgets: Optional[CategoryBudgetInput] = None

class SuggestionItem(SQLModel):
    title:       str
    description: str
    savings:     float

class BudgetSettingsResponse(SQLModel):
    AutoBudget:         bool
    TotalBudget:        int
    Food:               int
    Transport:          int
    Utilities:          int
    Entertainment:      int
    Shopping:           int
    Healthcare:         int
    Other:              int
    AutoComputedBudget: Optional[float] = None

class BudgetPageResponse(SQLModel):
    Settings:    BudgetSettingsResponse
    Suggestions: list[SuggestionItem]

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# settings stuff
class UserSettings(SQLModel):
    MonthlyIncome: float = Field(default=0.0, ge=0)
    HouseholdSize: int = Field(default=1, ge=1)
    TransportationTypes: list[TransportationType] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    MonthlyTransportSpending: float = Field(default=0.0, ge=0)
    MonthlyUtilityBill: float = Field(default=0.0, ge=0)
    PriceIncreaseAlerts: bool = True
    BudgetThresholdAlerts: bool = True
    # AlertThreshold: int = Field(default=80, ge=1, le=100)
    PriceThreshold: int | None = Field(default=None, ge=1, le=100)
    BudgetThreshold: int | None = Field(default=None, ge=1, le=100)

class UserSettingsDB(UserSettings, table=True):
    __tablename__ = "user_settings"  # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key="user_details.Id", index=True, ondelete="CASCADE")
    Email: EmailStr # same email used for account creation
    SetupMode: str = "none" # "none" | "quick" | "detailed" | "skipped"
    SetupCompleted: bool = False

    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    UserDetails: "UserDetails" = Relationship(back_populates="UserSettings")

class QuickSetup(SQLModel):
    MonthlyIncome: float = Field(ge=0)

# class UserSetup(SQLModel):
#     MonthlyIncome: float
#     HouseholdSize: int 
#     TransportationTypes: list[TransportationType] = Field(default_factory=list) # tells postgres it is storing a list unique to everybody
#     PriceIncreaseAlerts: bool = True
#     BudgetThresholdAlerts: bool = True
#     AlertThreshold: int = Field(default=80, ge=1, le=100)

class UserSettingsUpdate(SQLModel):
    MonthlyIncome: float | None = Field(default=None, ge=0)
    HouseholdSize: int | None = Field(default=None, ge=1)
    TransportationTypes: list[TransportationType] | None = None
    MonthlyTransportSpending: float | None = Field(default=None, ge=0)
    MonthlyUtilityBill: float | None = Field(default=None, ge=0)
    PriceIncreaseAlerts: bool | None = None
    BudgetThresholdAlerts: bool | None = None
    AlertThreshold: int | None = Field(default=None, ge=1, le=100)
    PriceThreshold: int | None = Field(default=None, ge=1, le=100)
    BudgetThreshold: int | None = Field(default=None, ge=1, le=100)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# import expenses stuff
class PreviousExpense(SQLModel):
    Month: str = Field(min_length=7, max_length=7, description="format: YYYY-MM")
    Food: float = Field(default=0.0, ge=0)
    Transport: float = Field(default=0.0, ge=0)
    Utilities: float = Field(default=0.0, ge=0)
    Entertainment: float = Field(default=0.0, ge=0)
    Shopping: float = Field(default=0.0, ge=0)
    Healthcare: float = Field(default=0.0, ge=0)

    @field_validator("Month")
    @classmethod
    def validate_month(cls, value: str):
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise ValueError("Month must be in YYYY-MM format.")
        return value

class PreviousExpenseDB(PreviousExpense, table=True):
    __tablename__ = "previous_expenses" # type: ignore
    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key = "user_details.Id", index=True, ondelete="CASCADE")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )    
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    UserDetails: "UserDetails" = Relationship(back_populates="PreviousExpenses")

class AllPreviousExpenses(SQLModel):
    AllExpenseRows: list[PreviousExpense]

    @field_validator("AllExpenseRows")
    @classmethod
    def validate_unique_months(cls, value):
        months = [e.Month for e in value]
        if len(months) != len(set(months)):
            raise ValueError("Duplicate months are not allowed.")
        return value
    
class DeleteExpensesRequest(SQLModel):
    expenses_ids: list[int]

#------------------------------------------------------------------------------------------------
#alerts stuff
class AlertBase(SQLModel):
    Title: str
    Message: str
    AlertType: str # use enums instead?

class AlertCheck(AlertBase):
    IsRead: bool = False

class AlertDB(AlertCheck, table=True):
    __tablename__ = "user_alerts" # type: ignore

    Id: int | None = Field(default=None, primary_key=True)
    UserId: int = Field(foreign_key="user_details.Id", index=True, ondelete="CASCADE")
    CreatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    UpdatedAt: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )
    ReadAt: datetime | None = Field(default=None)
    UserDetails: "UserDetails" = Relationship(back_populates="UserAlerts")

    













