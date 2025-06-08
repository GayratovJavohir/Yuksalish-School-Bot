# bot/utils.py
import logging
import io
from aiogram import Bot

logger = logging.getLogger(__name__)

async def download_file_from_telegram(bot: Bot, file_id: str) -> io.BytesIO:
    """Async function to download Telegram file into BytesIO."""
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        downloaded_bytes_io = io.BytesIO()
        await bot.download_file(file_path, destination=downloaded_bytes_io)
        downloaded_bytes_io.seek(0) # Reset stream position to the beginning
        return downloaded_bytes_io
    except Exception as e:
        logger.error(f"Error downloading file from Telegram: {e}")
        raise

