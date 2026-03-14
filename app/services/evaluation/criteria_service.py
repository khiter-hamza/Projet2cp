from schemas.application import ApplicationResponse
from app.core.database import AsyncSessionLocal
from sqlalchemy import select ,func
from app.models.user import User
from app.models.application import Application
from app.schemas.application  import ScoreResponse




async def calculate_score(db : AsyncSessionLocal , user_id : int) ->ScoreResponse :
    score = 0
    n_application= await db.execute(select(func.count()).select_from(Application).where(Application.user_id == user_id).as_scalar())
    n_CompletedApplication = await db.execute(select(func.count()).select_from(Application).where(Application.status == "termine"))
    
    score+=5 if n_application != 0 else  0
    score +=5 if n_CompletedApplication != 0 else 0 
    
    
    
    return ScoreResponse(score=score , completed=n_CompletedApplication , applications=n_application)