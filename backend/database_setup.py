"""
Database setup script for LifeCoach AI
Run this once to initialize the database schema
"""
import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import engine, Base

logging.basicConfig(level=logging.INFO)

async def setup_database():
    """Setup database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Database setup completed")

    except Exception as e:
        logging.error(f"Database setup error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(setup_database())