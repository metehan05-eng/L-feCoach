from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
import sys
import os
sys.path.append(os.path.dirname(__file__))

from auth import get_current_user
from database import async_session, JournalEntry
from datetime import datetime, timezone

class JournalEntryCreate(BaseModel):
    title: str
    content: str

class JournalEntryUpdate(BaseModel):
    title: str = None
    content: str = None

router = APIRouter()

@router.get("/journal/entries")
async def get_journal_entries(current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(JournalEntry).where(JournalEntry.user_email == current_user).order_by(JournalEntry.created_at.desc())
            )
            entries = result.scalars().all()
            return [{"id": e.id, "title": e.title, "content": e.content, "created_at": e.created_at.isoformat(), "updated_at": e.updated_at.isoformat() if e.updated_at else None} for e in entries]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/journal/entries")
async def create_journal_entry(entry: JournalEntryCreate, current_user: str = Depends(get_current_user)):
    try:
        now = datetime.now(timezone.utc)
        async with async_session() as session:
            new_entry = JournalEntry(
                user_email=current_user,
                title=entry.title,
                content=entry.content,
                created_at=now,
                updated_at=now
            )
            session.add(new_entry)
            await session.commit()
            await session.refresh(new_entry)
            return {"id": new_entry.id, "title": new_entry.title, "content": new_entry.content, "created_at": new_entry.created_at.isoformat(), "updated_at": new_entry.updated_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/journal/entries/{entry_id}")
async def update_journal_entry(entry_id: int, entry: JournalEntryUpdate, current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.user_email == current_user)
            )
            db_entry = result.scalar_one_or_none()
            if not db_entry:
                raise HTTPException(status_code=404, detail="Entry not found")

            if entry.title is not None:
                db_entry.title = entry.title
            if entry.content is not None:
                db_entry.content = entry.content
            db_entry.updated_at = datetime.now(timezone.utc)

            await session.commit()
            return {"id": db_entry.id, "title": db_entry.title, "content": db_entry.content, "created_at": db_entry.created_at.isoformat(), "updated_at": db_entry.updated_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/journal/entries/{entry_id}")
async def delete_journal_entry(entry_id: int, current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.user_email == current_user)
            )
            db_entry = result.scalar_one_or_none()
            if not db_entry:
                raise HTTPException(status_code=404, detail="Entry not found")

            await session.delete(db_entry)
            await session.commit()
            return {"message": "Entry deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")