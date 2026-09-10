from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_user
from src.models import User
from src.schemas import PortfolioSummaryResponse
from src.services.portfolio import get_user_portfolio

router = APIRouter(prefix="/portfolio", tags=["Portfolio & Holdings"])

@router.get("", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(current_user:Annotated[User, Depends(get_current_user)],
                                db:Annotated[Session, Depends(get_db)]) :

    return await get_user_portfolio(user=current_user, db=db)