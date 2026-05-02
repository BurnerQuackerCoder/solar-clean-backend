from telegram import Bot
from app.core.config import settings

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

async def send_message(chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False