from fastapi import Response, status, HTTPException, Depends, APIRouter
from typing import Annotated
from ..utils.auth import get_password_hash, verify_password
from ..utils.email import send_verification_email, send_password_reset_email, generate_verification_code, generate_reset_code, get_verification_code_expiry, get_reset_token_expiry
from ..models import *
from ..oauth2 import get_current_active_user, get_user
from ..database import *
from datetime import datetime, timezone
from sqlmodel import select

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register_user(user: UserCreate, db: SessionDependency):
    existing_user = get_user(db, email=user.Email)

    # existing (not yet verified code) user
    if existing_user:
        # If they are already verified, we throw the usual error
        if existing_user.EmailVerified:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # If they exist but ARE NOT verified (the "stuck" state):
        # We update their info and send a new code (effectively a "resend")
        existing_user.HashedPassword = get_password_hash(user.Password)
        verification_code = generate_verification_code()
        existing_user.VerificationCode = verification_code
        existing_user.VerificationCodeExpiry = get_verification_code_expiry()

        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)

        # Send the new verification email
        email_sent = send_verification_email(user.Email, verification_code)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again."
            )

        return existing_user

    # new user flow
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

# delete account and related tables (cascade)
@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(payload: UserDeleteAccount, current_user: CurrentUser,db: SessionDependency):
    # 1. Validation Check
    if not (payload.IsSure and payload.DataDelete):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm account and data deletion."
        )

    # 2. Password Verification
    if not verify_password(payload.Password, current_user.HashedPassword):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The password you entered is incorrect."
        )

    db.delete(current_user)
    db.commit()
    
    return None # 204 No Content typically returns nothing

# prompt user for current password before changing password
@router.put("/verify-password", status_code=status.HTTP_202_ACCEPTED, response_model=UserResponse)
def verify_user_password(payload: UserVerifyPassword, current_user: CurrentUser, db: SessionDependency):
    # 1. Verify the provided current password against the stored hash
    is_valid = verify_password(payload.Password, current_user.HashedPassword)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The password you entered is incorrect."
        )

    return current_user

# change password and update databse
@router.put("/change-password", status_code=status.HTTP_202_ACCEPTED, response_model=UserResponse)
def change_user_password(payload: UserChangePassword, current_user: CurrentUser, db: SessionDependency):
    new_pw = payload.Password
    re_new_pw = payload.RePassword

    if not new_pw == re_new_pw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The passwords do not match."
        )
    
    hashed_new_pw = get_password_hash(new_pw)
    current_user.HashedPassword = hashed_new_pw

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user

# Verify email after registration
@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(payload: VerifyEmailRequest, db: SessionDependency):
    """User submits their email and verification code"""
    
    # 1. Find the user
    user = get_user(db, email=payload.Email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 2. Check if already verified
    if user.EmailVerified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # 3. Check if code matches
    if user.VerificationCode != payload.VerificationCode:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code"
        )
    
    # 4. Check if code expired
    # Force the database time to act as UTC so it can be compared to the aware "now"
    if user.VerificationCodeExpiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification code expired"
        )
    
    # 5. Mark email as verified and activate user
    user.EmailVerified = True
    user.Active = True
    user.VerificationCode = None  # Clear the code
    user.VerificationCodeExpiry = None
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"detail": "Email verified successfully. You can now log in."}


# Request password reset
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: ForgotPasswordRequest, db: SessionDependency):
    """User requests password reset by providing their email"""
    
    # 1. Find the user
    user = get_user(db, email=payload.Email)
    if not user:
        # Don't reveal if email exists (security best practice)
        return {"detail": "If this email exists, you will receive a password reset code"}
    
    # 2. Generate reset token/code
    reset_code = generate_reset_code()
    
    # 3. Save hashed version and expiry to DB
    user.ResetToken = reset_code  # In production, hash this too
    user.ResetTokenExpiry = get_reset_token_expiry()
    
    db.add(user)
    db.commit()
    
    # 4. Send email with reset code
    email_sent = send_password_reset_email(payload.Email, reset_code)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email. Please try again."
        )
    
    return {"detail": "If this email exists, you will receive a password reset code"}


# Reset password with code
@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: SessionDependency):
    """User resets password using the code from email"""
    
    # 1. Find the user
    user = get_user(db, email=payload.Email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 2. Check if reset token exists
    if not user.ResetToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No password reset request found. Please use forgot-password first."
        )
    
    # 3. Check if token matches
    if user.ResetToken != payload.ResetCode:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset code"
        )
    
    # 4. Check if token expired
    if user.ResetTokenExpiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset code expired. Please request a new one."
        )
    
    # 5. Update password
    new_hashed_pw = get_password_hash(payload.NewPassword)
    user.HashedPassword = new_hashed_pw
    user.ResetToken = None  # Clear the token
    user.ResetTokenExpiry = None
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"detail": "Password reset successfully. You can now log in with your new password."}