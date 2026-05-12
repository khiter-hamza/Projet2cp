from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter()


class EvaluationCriterionResponse(BaseModel):
    key: str
    label: str
    weight: int
    type: str
    is_active: bool


def can_view_settings(user: User) -> bool:
    return user.role.value in ["assistant_dpgr", "admin_dpgr", "super_admin"]


@router.get("/evaluation-criteria", response_model=list[EvaluationCriterionResponse])
async def get_evaluation_criteria(user: User = Depends(get_current_user)):
    if not can_view_settings(user):
        raise HTTPException(status_code=403, detail="Not authorized")

    return [
        EvaluationCriterionResponse(
            key="stays_consumed",
            label="Stays consumed",
            weight=50,
            type="Required Priority",
            is_active=True,
        ),
        EvaluationCriterionResponse(
            key="last_stay_date",
            label="Last stay date",
            weight=50,
            type="Required Priority",
            is_active=True,
        ),
    ]
