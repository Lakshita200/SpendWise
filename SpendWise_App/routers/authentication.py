# code for the login function/path
from datetime import timedelta
from typing import Annotated
from fastapi import Body, Depends, HTTPException, status
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from ..models import Token, TokenData
from ..database import SessionDependency
from ..oauth2 import * 
# from ..schema import TokenData

router = APIRouter(
    tags = ["Authentication"]
)


# route for logging in
@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDependency
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # active check for accounts that do not verify their email
    if not user.Active:
        if not user.EmailVerified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email before logging in."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated or suspended."
            )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = TokenData(Sub=user.Email)

    access_token = create_access_token(data=token_data.model_dump(), expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=token_data.model_dump())

    statement = select(UserDetails).where(UserDetails.Email == user.Email)
    results = db.exec(statement)
    user_db = results.first()

    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User details not found"
        )
        
    user_db.RefreshToken = refresh_token

    db.add(user_db)
    db.commit()

    return Token(
        AccessToken=access_token, 
        RefreshToken=refresh_token, 
        TokenType="bearer",
        UserType=user.UserType
    )

#logout -> must change to inactive user? 
@router.post("/logout")
async def logout(
    current_user: Annotated[UserDetails, Depends(get_current_active_user)], 
    db: SessionDependency
):
    #sqlmodel auto tracks and will update instead of adding a new instance?
    current_user.RefreshToken = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return {"detail": "Successfully logged out"}

# called when access expires 
# depends get_curret_active_user fails
@router.post("/refresh")
async def refresh_access_token(
    # We expect the frontend to send the refresh_token in the body
    refresh_token: Annotated[str, Body()], 
    db: SessionDependency
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(refresh_token, credentials_exception=credentials_exception, SECRET_KEY=SECRET_KEY, ALGORITHM=ALGORITHM)

    user = get_user(db, email=token_data.Sub)
    # checks if user exists and if this is their token 
    # checks if the refresh token still exists in the db (user has not logged out)
    if user is None or user.RefreshToken != refresh_token:
        raise credentials_exception

    # 4. Issue a brand new Access Token
    new_access_token = create_access_token(data=token_data.model_dump())

    return {
        "AccessToken": new_access_token,
        "TokenType": "bearer"
    }
