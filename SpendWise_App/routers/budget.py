from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from ..database import SessionDependency
from ..models import UserBudgetDB, CategoryBudgetInput, BudgetSettingsRequest, BudgetSettingsResponse, BudgetPageResponse, SuggestionItem, UserDetails
from ..oauth2 import get_current_active_user
from ..utils.utils import get_or_create_budget
from ..utils.calculations import compute_category_budgets, build_budget_suggestions, compute_auto_budget, compute_budget_data


router = APIRouter(prefix="/budget", tags=["Budget"])

CurrentUser = Annotated[UserDetails, Depends(get_current_active_user)]


# ── Endpoints ─────────────────────────────────────────────────

@router.get("", response_model=BudgetPageResponse)
def get_budget_page(
session: SessionDependency,current_user: CurrentUser,):
    """Single call that powers the full Budget page on load."""
    budget     = get_or_create_budget(current_user.Id, session)
    auto_value = compute_auto_budget(current_user.Id, session) if budget.AutoBudget else None
    suggestions = build_budget_suggestions(current_user.Id, session)

    return BudgetPageResponse(
        Settings=BudgetSettingsResponse(
            AutoBudget=budget.AutoBudget,
            TotalBudget=budget.TotalBudget,
            Food=budget.Food,
            Transport=budget.Transport,
            Utilities=budget.Utilities,
            Entertainment=budget.Entertainment,
            Shopping=budget.Shopping,
            Healthcare=budget.Healthcare,
            Other=budget.Other,
            AutoComputedBudget=auto_value,
        ),
        Suggestions=[SuggestionItem(**s) for s in suggestions],
    )


# @router.post("/settings", response_model=BudgetSettingsResponse)
# def save_budget_settings(
#     payload: BudgetSettingsRequest,
#     session: SessionDependency,
#     current_user: CurrentUser,
# ):
#     """
#     AUTO mode   → computes TotalBudget from last 3 months, clears category fields
#     MANUAL mode → requires TotalBudget, optional category splits
#     """
#     if not payload.AutoBudget and not payload.TotalBudget:
#         raise HTTPException(status_code=422, detail="TotalBudget is required for manual mode")

#     budget = get_or_create_budget(current_user.Id, session)
#     budget.AutoBudget = payload.AutoBudget

#     if payload.AutoBudget:
#         budget.TotalBudget    = int(compute_auto_budget(current_user.Id, session))
#         budget.Food           = 0
#         budget.Transport      = 0
#         budget.Utilities      = 0
#         budget.Entertainment  = 0
#         budget.Shopping       = 0
#         budget.Healthcare     = 0
#         budget.Other          = 0

#     else:
#         budget.TotalBudget = payload.TotalBudget  # type: ignore

#         if payload.CategoryBudgets:
#             cb = payload.CategoryBudgets
#             total_cat = sum(filter(None, [
#                 cb.Food, cb.Transport, cb.Utilities,
#                 cb.Entertainment, cb.Shopping, cb.Healthcare, cb.Other
#             ]))
#             if total_cat > payload.TotalBudget:
#                 raise HTTPException(
#                     status_code=422,
#                     detail=f"Category budgets (${total_cat:,}) exceed TotalBudget (${payload.TotalBudget:,})"
#                 )
#             budget.Food          = cb.Food          or 0
#             budget.Transport     = cb.Transport     or 0
#             budget.Utilities     = cb.Utilities     or 0
#             budget.Entertainment = cb.Entertainment or 0
#             budget.Shopping      = cb.Shopping      or 0
#             budget.Healthcare    = cb.Healthcare    or 0
#             budget.Other         = cb.Other         or 0
#         else:
#             # All blank → frontend shows "Auto" placeholder per category
#             budget.Food = budget.Transport = budget.Utilities = 0
#             budget.Entertainment = budget.Shopping = budget.Healthcare = budget.Other = 0

#     session.add(budget)
#     session.commit()
#     session.refresh(budget)

#     return BudgetSettingsResponse(
#         AutoBudget=budget.AutoBudget,
#         TotalBudget=budget.TotalBudget,
#         Food=budget.Food,
#         Transport=budget.Transport,
#         Utilities=budget.Utilities,
#         Entertainment=budget.Entertainment,
#         Shopping=budget.Shopping,
#         Healthcare=budget.Healthcare,
#         Other=budget.Other,
#         AutoComputedBudget=float(budget.TotalBudget) if budget.AutoBudget else None,
#     )

@router.post("/settings", response_model=BudgetSettingsResponse)
def save_budget_settings(
    payload: BudgetSettingsRequest,
    session: SessionDependency,
    current_user: CurrentUser,
):
    if not payload.AutoBudget and not payload.TotalBudget:
        raise HTTPException(status_code=422, detail="TotalBudget is required for manual mode")

    budget = get_or_create_budget(current_user.Id, session)
    budget.AutoBudget = payload.AutoBudget
    cat_avgs = compute_category_budgets(current_user.Id, session)

    budget_data = compute_budget_data(current_user.Id, session)

    if payload.AutoBudget:
        auto_total = int(budget_data["auto_total"])
        proportions = budget_data["category_proportions"]
        categories = ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]

        budget.TotalBudget = auto_total

        allocated = {cat: int(auto_total * proportions[cat]) for cat in categories}
        remainder = auto_total - sum(allocated.values())
        largest = max(allocated, key=allocated.get)
        allocated[largest] += remainder

        new_budget = UserBudgetDB(
            UserId=current_user.Id,
            AutoBudget=True,
            TotalBudget=auto_total,
            Food=allocated["Food"],
            Transport=allocated["Transport"],
            Utilities=allocated["Utilities"],
            Entertainment=allocated["Entertainment"],
            Shopping=allocated["Shopping"],
            Healthcare=allocated["Healthcare"],
            Other=allocated["Other"]
        )

    else:
        budget.TotalBudget = payload.TotalBudget

        cb = payload.CategoryBudgets
        filled = {}
        blank_keys = []
        categories = ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]

        for cat in categories:
            user_val = getattr(cb, cat, None) if cb else None
            if user_val:
                filled[cat] = user_val
            else:
                blank_keys.append(cat)

        blank_vals = {cat: cat_avgs[cat] for cat in blank_keys}

        total_filled = sum(filled.values())
        total_blank  = sum(blank_vals.values())
        total_all    = total_filled + total_blank

        if total_all != payload.TotalBudget:
            if total_all > payload.TotalBudget:
                exceeded = total_all - payload.TotalBudget
                raise HTTPException(
                    status_code=422,
                    detail=f"Category budgets (${total_all:,.2f}) exceed Total Budget (${payload.TotalBudget:,.2f}) by ${exceeded:,.2f}. Please reduce your category values."
                )
            else:
                shortfall = payload.TotalBudget - total_all
                raise HTTPException(
                    status_code=422,
                    detail=f"Category budgets (${total_all:,.2f}) are below Total Budget (${payload.TotalBudget:,.2f}) by ${shortfall:,.2f}. Please increase your category values."
                )
        final = {**filled, **blank_vals}

        new_budget = UserBudgetDB(
            UserId=current_user.Id,
            AutoBudget=False,
            TotalBudget=payload.TotalBudget,
            Food=final["Food"],
            Transport=final["Transport"],
            Utilities=final["Utilities"],
            Entertainment=final["Entertainment"],
            Shopping=final["Shopping"],
            Healthcare=final["Healthcare"],
            Other=final["Other"]
        )

    session.add(new_budget)
    session.commit()
    session.refresh(new_budget)

    return BudgetSettingsResponse(
        AutoBudget=budget.AutoBudget,
        TotalBudget=budget.TotalBudget,
        Food=budget.Food,
        Transport=budget.Transport,
        Utilities=budget.Utilities,
        Entertainment=budget.Entertainment,
        Shopping=budget.Shopping,
        Healthcare=budget.Healthcare,
        Other=budget.Other,
        AutoComputedBudget=float(budget.TotalBudget) if budget.AutoBudget else None,
    )