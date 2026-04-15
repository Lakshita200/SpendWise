from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, select
from ..database import SessionDependency
from ..models import UserDetails, UserSettingsDB
from ..oauth2 import get_current_active_user
from ..utils import get_or_create_budget
from ..calculations import compute_auto_budget, build_budget_suggestions


router = APIRouter(prefix="/alerts", tags=["Alerts"])

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]

# threshold to alert the user when budget reaches certain threshold
def get_user_thresholds(db: Session, user_id: int, type: str):
    statement = select(UserSettingsDB).where(UserSettingsDB.UserId == user_id)
    settings = db.exec(statement).first()
    if not settings:
        raise HTTPException(
            status_code=404, 
            detail="User Settings Does Not Exists."
        )
    if type == "budget":
        result = settings.BudgetThreshold
    elif type == "price":
        result = settings.PriceThreshold
    else:
        result = settings.AlertThreshold
    return result 


@router.get("/budget-warning")
def budget_warning_alert(current_user: CurrentUser, db: SessionDependency):
    userid = current_user.Id
    if not userid:
        raise HTTPException(status_code=404, detail="User Does Not Exists.")
    
    threshold = get_user_thresholds(db, userid, "budget")




@router.get("/price-increase")
def price_increase_alert(current_user: CurrentUser, db: SessionDependency):
    userid = current_user.Id
    if not userid:
        raise HTTPException(status_code=404, detail="User Does Not Exists.")
    
    threshold = get_user_thresholds(db, userid, "price")



@router.get("/")
def alert(current_user: CurrentUser, db: SessionDependency):
    userid = current_user.Id




# old login page 
<div className="welcome">
          <h1>SpendWise</h1>
          <div className="tab-buttons">
            <button className={`tab-btn ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>
              Sign In
            </button>
            <button className={`tab-btn ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>
              Sign Up
            </button>
          </div>

          {isLogin ? (
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <input
                  type="email"
                  placeholder="Email"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="password"
                  placeholder="Password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  required
                />
              </div>
              <button type="submit" className="btn">
                Sign In
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignup}>
              <div className="form-group">
                <input
                  type="email"
                  placeholder="Email"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
              <input
                type="password"
                placeholder="Password"
                value={loginForm.password}
                onChange={(e) => {
                  const value = e.target.value;

                  setLoginForm((prev) => ({
                    ...prev,
                    password: value
                  }));

                  // 🔥 THIS is the missing link
                  if (!isLogin) {
                    setPasswordErrors(validatePassword(value));
                  }
                }}
                required
              />

              {!isLogin && passwordErrors.length > 0 && (
                <div className="error" style={{ marginTop: '10px' }}>
                  {passwordErrors.map((err, idx) => (
                    <div key={idx}>{err}</div>
                  ))}
                </div>
              )}
            </div>
              <button type="submit" className="btn">
                Sign Up
              </button>
            </form>
          )}
        </div>


# old handlesignups code 

const handleSignup = async (e) => {
    e.preventDefault();

    const email = loginForm.username.trim();
    const password = loginForm.password;

    const clientErrors = validatePassword(password);
    setPasswordErrors(clientErrors);

    if (clientErrors.length > 0) {
      showToast('Please fix your password before signing up.');
      return;
    }

    try {
      const res = await fetch(`/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Email: email,
          Password: password
        })
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setPasswordErrors([]);
        showToast('Account created! Sign in now.');
        setIsLogin(true);
        setLoginForm({ username: '', password: '' });
        return;
      }

      // Handle FastAPI/Pydantic validation errors safely
      let message = 'Failed to create account';

      if (typeof data?.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data?.detail)) {
        const extracted = data.detail
          .map((item) => item?.msg)
          .filter(Boolean);

        if (extracted.length > 0) {
          message = extracted.join(' ');
          setPasswordErrors(extracted);
        }
      }

      showToast(message);
    } catch (err) {
      showToast('Error: ' + err.message);
    }
  };


# old verify change and forgot password handlers 

const handleVerifyPassword = async () => {
    if (!securityForm.currentPassword) {
      showToast('Enter current password.');
      return;
    }
    setSavingSecurity(true);
    try {
      const res = await fetchWithAuth(`/users/verify-password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Password: securityForm.currentPassword })
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast('Password verified.');
      } else {
        showToast(data.detail || 'Password verification failed');
      }
    } catch (err) {
      showToast('Error verifying password: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };

  const handleChangePassword = async () => {
    if (!securityForm.newPassword || !securityForm.reNewPassword) {
      showToast('Enter new password and confirmation.');
      return;
    }
    setSavingSecurity(true);
    try {
      const res = await fetchWithAuth(`/users/change-password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Password: securityForm.newPassword, RePassword: securityForm.reNewPassword })
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast('Password updated.');
        setSecurityForm((prev) => ({ ...prev, newPassword: '', reNewPassword: '' }));
      } else {
        showToast(data.detail || 'Failed to update password');
      }
    } catch (err) {
      showToast('Error changing password: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };

  const handleForgotPassword = async () => {
    const email = (securityForm.forgotEmail || loginForm.username || '').trim();
    if (!email) {
      showToast('Enter an email for recovery.');
      return;
    }
    setSavingSecurity(true);
    try {
      const res = await fetchWithAuth(`/users/forgot-password?email=${encodeURIComponent(email)}`, {
        method: 'POST'
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast(data.msg || 'Recovery flow started.');
      } else {
        showToast(data.detail || 'Failed to start recovery flow');
      }
    } catch (err) {
      showToast('Error starting recovery flow: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };


  # old settings page middle parts 

                      <div className="section-title">Account Security</div>
                    <div className="form-group">
                      <label>Current Password</label>
                      <input
                        type="password"
                        value={securityForm.currentPassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, currentPassword: e.target.value }))}
                      />
                    </div>
                    <button className="btn btn-secondary" type="button" onClick={handleVerifyPassword} disabled={savingSecurity}>
                      Verify Current Password
                    </button>

                    <div className="form-group" style={{ marginTop: '12px' }}>
                      <label>New Password</label>
                      <input
                        type="password"
                        value={securityForm.newPassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, newPassword: e.target.value }))}
                      />
                    </div>
                    <div className="form-group">
                      <label>Re-enter New Password</label>
                      <input
                        type="password"
                        value={securityForm.reNewPassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, reNewPassword: e.target.value }))}
                      />
                    </div>
                    <button className="btn btn-secondary" type="button" onClick={handleChangePassword} disabled={savingSecurity}>
                      Change Password
                    </button>

                    <div className="form-group" style={{ marginTop: '12px' }}>
                      <label>Recovery Email</label>
                      <input
                        type="email"
                        value={securityForm.forgotEmail}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, forgotEmail: e.target.value }))}
                        placeholder="you@example.com"
                      />
                    </div>
                    <button className="btn btn-secondary" type="button" onClick={handleForgotPassword} disabled={savingSecurity}>
                      Forgot Password
                    </button>

                    <div className="section-title">Danger Zone</div>
                    <div className="form-group">
                      <label>Confirm Password To Delete Account</label>
                      <input
                        type="password"
                        value={securityForm.deletePassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, deletePassword: e.target.value }))}
                      />
                    </div>
                    <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <input
                        type="checkbox"
                        className="checkbox"
                        checked={securityForm.deleteConfirm}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, deleteConfirm: e.target.checked }))}
                      />
                      <label style={{ margin: 0 }}>I understand this permanently deletes my account and data.</label>
                    </div>
                    <button
                      className="btn btn-secondary"
                      type="button"
                      style={{ marginTop: '8px', background: '#ffe0e0', color: '#7f1d1d' }}
                      onClick={handleDeleteAccount}
                      disabled={savingSecurity}
                    >
                      Delete Account
                    </button>


# second version of handlersignup 
  const handleSignup = async (e) => {
    e.preventDefault();

    // NEW: Frontend check for Terms and Conditions
    if (!termsAccepted) {
      showToast('You must agree to the Terms and Conditions to proceed.');
      return;
    }

    const email = loginForm.username.trim();
    const password = loginForm.password;

    const clientErrors = validatePassword(password);
    setPasswordErrors(clientErrors);

    if (clientErrors.length > 0) {
      showToast('Please fix your password before signing up.');
      return;
    }

    try {
      const res = await fetch(`/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Email: email,
          Password: password
        })
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setPasswordErrors([]);
        showToast('Account created! Sign in now.');
        setIsLogin(true);
        setLoginForm({ username: '', password: '' });
        setTermsAccepted(false); // reset checkbox
        return;
      }

      // Handle FastAPI/Pydantic validation errors safely
      let message = 'Failed to create account';
      if (typeof data?.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data?.detail)) {
        const extracted = data.detail.map((item) => item?.msg).filter(Boolean);
        if (extracted.length > 0) {
          message = extracted.join(' ');
          setPasswordErrors(extracted);
        }
      }
      showToast(message);
    } catch (err) {
      showToast('Error: ' + err.message);
    }
  };


  # second version of handlerforgot

  const handleForgotPassword = async () => {
    const email = forgotEmailInput.trim();
    if (!email) {
      showToast('Enter an email for recovery.');
      return;
    }
    setSavingSecurity(true);
    try {
      // Note: We use a standard fetch here in case they are logged out
      const res = await fetch(`/users/forgot-password?email=${encodeURIComponent(email)}`, {
        method: 'POST'
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast(data.msg || 'Recovery flow started. Check your email.');
        setShowForgotModal(false);
        setForgotEmailInput('');
      } else {
        showToast(data.detail || 'Failed to start recovery flow');
      }
    } catch (err) {
      showToast('Error starting recovery flow: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };
