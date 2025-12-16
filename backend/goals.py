from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
import sys
import os
sys.path.append(os.path.dirname(__file__))

from auth import get_current_user
from database import async_session, Goal
from datetime import datetime, timezone

class GoalCreate(BaseModel):
    title: str
    description: str

class GoalUpdate(BaseModel):
    title: str = None
    description: str = None
    progress: int = None

router = APIRouter()

@router.get("/goals")
async def get_goals(current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Goal).where(Goal.user_email == current_user).order_by(Goal.created_at.desc())
            )
            goals = result.scalars().all()
            return [{"id": g.id, "title": g.title, "description": g.description, "progress": g.progress, "created_at": g.created_at.isoformat(), "updated_at": g.updated_at.isoformat() if g.updated_at else None} for g in goals]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/goals")
async def create_goal(goal: GoalCreate, current_user: str = Depends(get_current_user)):
    try:
        now = datetime.now(timezone.utc)
        async with async_session() as session:
            new_goal = Goal(
                user_email=current_user,
                title=goal.title,
                description=goal.description,
                progress=0,
                created_at=now,
                updated_at=now
            )
            session.add(new_goal)
            await session.commit()
            await session.refresh(new_goal)
            return {"id": new_goal.id, "title": new_goal.title, "description": new_goal.description, "progress": new_goal.progress, "created_at": new_goal.created_at.isoformat(), "updated_at": new_goal.updated_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/goals/{goal_id}")
async def update_goal(goal_id: int, goal: GoalUpdate, current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Goal).where(Goal.id == goal_id, Goal.user_email == current_user)
            )
            db_goal = result.scalar_one_or_none()
            if not db_goal:
                raise HTTPException(status_code=404, detail="Goal not found")

            if goal.title is not None:
                db_goal.title = goal.title
            if goal.description is not None:
                db_goal.description = goal.description
            if goal.progress is not None:
                db_goal.progress = max(0, min(100, goal.progress))  # Clamp between 0-100
            db_goal.updated_at = datetime.now(timezone.utc)

            await session.commit()
            return {"id": db_goal.id, "title": db_goal.title, "description": db_goal.description, "progress": db_goal.progress, "created_at": db_goal.created_at.isoformat(), "updated_at": db_goal.updated_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: int, current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Goal).where(Goal.id == goal_id, Goal.user_email == current_user)
            )
            db_goal = result.scalar_one_or_none()
            if not db_goal:
                raise HTTPException(status_code=404, detail="Goal not found")

            await session.delete(db_goal)
            await session.commit()
            return {"message": "Goal deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")