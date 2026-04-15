import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import ImportExpenses, admin, alerts, authentication, expenses, settings, categories, user, dashboard, basket, budget
from . import database



LOG_DIR = Path.cwd().parent / "spendwise_logs" 

try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    # Fallback to local logs if permission is denied in parent folder
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)
    print(f"Warning: Could not create parent log dir, using local: {e}")

LOG_FILE_PATH = LOG_DIR / "spendwise.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE_PATH)
    ]
)

from sqlmodel import Session, select
from .database import engine
from .models import UserDetails
from .utils.auth import get_password_hash

# master account and admin account
def create_master_account():
    with Session(engine) as session:
        # Check if master account already exists
        master_statement = select(UserDetails).where(UserDetails.Email == "master@gmail.com")
        admin_statement = select(UserDetails).where(UserDetails.Email == "admin@gmail.com")
        master = session.exec(master_statement).first()
        admin = session.exec(admin_statement).first()

        hashed_pw = get_password_hash("Pass123@")

        if not master:
            master_user = UserDetails(
                Email="master@gmail.com",
                HashedPassword=hashed_pw,
                UserType="user", # Or "user" based on your preference
                Active=True,      # Automatically Active
                EmailVerified=True # Skips the 6-digit code check
            )
            session.add(master_user)

        if not admin:
            admin_user = UserDetails(
                Email="admin@gmail.com",
                HashedPassword=hashed_pw,
                UserType="admin", # Or "user" based on your preference
                Active=True,      # Automatically Active
                EmailVerified=True # Skips the 6-digit code check
            )

            session.add(admin_user)
  
        session.commit()


# 1. THE LIFESPAN (The "Wake Up" Routine)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Powering up the Brain... Creating database tables.")
    database.create_db_and_tables()
    create_master_account()
    yield
    print("😴 Closing the Brain... Database connection shut down.")

app = FastAPI(lifespan=lifespan)

# include domains that are allowed to talk to the api (* --> wildcard)
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. THE ROUTERS (Connecting the different rooms)
app.include_router(admin.router)
app.include_router(alerts.router)
app.include_router(authentication.router)
app.include_router(basket.router)
app.include_router(budget.router)
app.include_router(categories.router)
app.include_router(dashboard.router)
app.include_router(expenses.router)
app.include_router(ImportExpenses.router)
app.include_router(settings.router)
app.include_router(user.router)



# root route
@app.get("/")
async def root():
    return {"message": "SpendWise API is officially LIVE!"}

