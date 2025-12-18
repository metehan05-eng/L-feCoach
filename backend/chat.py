from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
import sys
import os
sys.path.append(os.path.dirname(__file__))

from auth import get_current_user
from database import async_session, User, ChatHistory
import logging
from datetime import datetime, timezone, timedelta
import httpx
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
# Read Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class ChatMessage(BaseModel):
    message: str
    feature: str = "chat"


router = APIRouter()

async def get_user_data(email: str):
    """Get user data from database"""
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                return {
                    "user_type": "free",
                    "language": user.language or "tr",
                    "message_count": user.message_count or 0,
                    "last_message_date": user.last_message_date
                }
        return {"user_type": "free", "language": "tr", "message_count": 0, "last_message_date": None}
    except Exception as e:
        logging.error(f"Error getting user data: {str(e)}")
        return {"user_type": "free", "language": "tr", "message_count": 0, "last_message_date": None}

def check_message_limit(user_data: dict) -> tuple[bool, int]:
    """Check if user can send message and return remaining messages"""
    return True, -1  # Unlimited for all users

async def reset_message_count_if_needed(email: str, user_data: dict) -> bool:
    """Reset message count if cooldown period has passed. Returns True if reset occurred."""
    last_message_date = user_data.get("last_message_date")
    if not last_message_date:
        return False

    try:
        last_message_time = datetime.fromisoformat(last_message_date.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        cooldown_period = timedelta(hours=5)

        if current_time - last_message_time >= cooldown_period:
            # Reset count
            async with async_session() as session:
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                if user:
                    user.message_count = 0
                    user.last_message_date = None
                    await session.commit()
                    user_data["message_count"] = 0
                    user_data["last_message_date"] = None
                    return True
    except Exception as e:
        logging.error(f"Error resetting message count: {e}")

    return False

async def update_message_count(email: str, user_data: dict):
    """Update user's message count"""
    now = datetime.now(timezone.utc).isoformat()
    new_count = user_data["message_count"] + 1

    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user.message_count = new_count
                user.last_message_date = now
                await session.commit()
    except Exception as e:
        logging.error(f"Error updating message count: {str(e)}")

@router.post("/chat")
async def chat(message: ChatMessage, current_user: str = Depends(get_current_user)):
    try:
        # Get user data
        user_data = await get_user_data(current_user)
        
        # Try Ollama local server first (if available). Otherwise use built-in fallbacks.
        msg = message.message.lower()

        async def call_gemini(prompt: str) -> str | None:
            """Call Google Gemini API for AI response."""
            if not GEMINI_API_KEY:
                return None

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code != 200:
                        logging.debug(f"Gemini API returned status {resp.status_code}: {resp.text}")
                        return None

                    data = resp.json()
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if len(parts) > 0 and "text" in parts[0]:
                                return parts[0]["text"].strip()

            except Exception as e:
                logging.debug(f"Gemini call failed: {e}")

            return None

        # Try Gemini and use its response if it's meaningful (not just echo)
        try:
            gemini_text = await call_gemini(message.message)
            if gemini_text:
                gemini_text = gemini_text.strip()
                if gemini_text and gemini_text.lower() != message.message.lower():
                    ai_response = gemini_text
                    response_payload = {"text": ai_response, "source": "gemini", "model": "gemini-1.5-flash"}

                    # Save history and return
                    async with async_session() as session:
                        new_chat = ChatHistory(
                            user_email=current_user,
                            message=message.message,
                            response=response_payload["text"],
                            feature=message.feature,
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(new_chat)
                        await session.commit()

                    return {"response": response_payload, "remaining_messages": -1}
        except Exception:
            logging.debug("Ollama inference attempt raised an exception; continuing with fallback.")
        
        # Intelligent Turkish responses based on keywords
        if "merhaba" in msg or "selam" in msg or "hey" in msg or "hi" in msg:
            ai_response = "Merhaba! Nasılsın bugün? Hayatında sana nasıl yardımcı olabilirim? 😊"
        elif "yardım" in msg or "nasıl" in msg:
            ai_response = "Size motivasyon, hedef belirleme, duygusal destek veya günlük tutma konusunda yardımcı olabilirim. Ne hakkında konuşmak istersiniz?"
        elif "hedef" in msg or "amaç" in msg or "plan" in msg:
            ai_response = "Harika! Hedef belirlemek başarının ilk adımıdır. SMART hedefler (Spesifik, Ölçülebilir, Erişilebilir, İlgili, Zamanlı) oluşturmanıza yardımcı olabilirim. Ne tür bir hedef belirlemek istiyorsunuz?"
        elif "duygu" in msg or "üzgün" in msg or "mutlu" in msg or "kötü" in msg or "iyi" in msg:
            ai_response = "Duygularınızı paylaşmak cesaret ister ve çok değerlidir. Bu duyguları anlamanıza ve yönetmenize yardımcı olabilirim. Şu an ne hissediyorsunuz?"
        elif "motivasyon" in msg or "enerji" in msg or "isteksiz" in msg:
            ai_response = "Motivasyon bazen dalgalanabilir, bu çok normal. Size motivasyonunuzu artıracak stratejiler ve teknikler önerebilirim. Hangi alanda kendinizi daha motive hissetmek istiyorsunuz?"
        elif "stres" in msg or "kaygı" in msg or "endişe" in msg:
            ai_response = "Stres ve kaygı modern hayatın bir parçası. Bunlarla başa çıkmanıza yardımcı olacak teknikler öğretebilirim. Sizi en çok ne strese sokuyor?"
        elif "başarı" in msg or "kazanmak" in msg or "başarmak" in msg:
            ai_response = "Başarı yolculuğu küçük adımlarla başlar. Size başarıya ulaşmanız için bir yol haritası çizebilirim. Hangi alanda başarılı olmak istiyorsunuz?"
        elif "teşekkür" in msg or "sağol" in msg or "teşekkürler" in msg:
            ai_response = "Rica ederim! Size yardımcı olmaktan mutluluk duyuyorum. Başka bir konuda yardımcı olabilir miyim? 😊"
        elif "günaydın" in msg:
            ai_response = "Günaydın! Yeni bir gün, yeni fırsatlar demek. Bugün kendiniz için ne yapmak istersiniz?"
        elif "iyi geceler" in msg or "hoşçakal" in msg or "görüşürüz" in msg:
            ai_response = "İyi geceler! Yarın yeni bir gün olacak. Kendinize iyi bakın! 🌙"
        elif "kim" in msg and ("sen" in msg or "siz" in msg):
            ai_response = "Ben bir yapay zeka yaşam koçuyum. Sizin kişisel gelişiminize, hedeflerinize ulaşmanıza ve daha mutlu bir hayat sürmenize yardımcı olmak için buradayım."
        elif "nasılsın" in msg or "nasılsınız" in msg:
            ai_response = "Ben iyiyim, teşekkür ederim! Sizinle konuşmaktan mutluluk duyuyorum. Siz nasılsınız?"
        else:
            ai_response = "Anlıyorum. Bu konuda daha fazla detay verebilir misiniz? Size en iyi şekilde yardımcı olmak istiyorum. 💭"

        response_payload = {
            "text": ai_response,
            "source": "lifecoach-ai",
            "model": "built-in",
        }

        # Save chat history
        async with async_session() as session:
            new_chat = ChatHistory(
                user_email=current_user,
                message=message.message,
                response=response_payload["text"],
                feature=message.feature,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_chat)
            await session.commit()

        return {
            "response": response_payload,
            "remaining_messages": -1
        }

    except Exception as e:
        logging.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/chat/history")
async def get_chat_history(current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(ChatHistory).where(ChatHistory.user_email == current_user).order_by(ChatHistory.created_at)
            )
            chats = result.scalars().all()
            return [{"message": c.message, "response": c.response, "created_at": c.created_at.isoformat()} for c in chats]
    except Exception as e:
        logging.error(f"History error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")