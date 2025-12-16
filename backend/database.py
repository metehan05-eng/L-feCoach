from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./lifecoach.db")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_premium = Column(Boolean, default=False)
    language = Column(String, default="tr")
    message_count = Column(Integer, default=0)
    last_message_date = Column(String, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, nullable=True)  # active, canceled, past_due, etc.

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    message = Column(Text)
    response = Column(Text)
    feature = Column(String, default="chat")
    created_at = Column(DateTime, default=None)

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=None)
    updated_at = Column(DateTime, default=None)

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    progress = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime, default=None)
    updated_at = Column(DateTime, default=None)

async def get_db():
    async with async_session() as session:
        yield session