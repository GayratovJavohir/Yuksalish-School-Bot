import asyncio
from django.core.management.base import BaseCommand
from bot.telegram_bot import main as run_telegram_bot

class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        self.stdout.write("Starting the Telegram bot...")
        asyncio.run(run_telegram_bot())