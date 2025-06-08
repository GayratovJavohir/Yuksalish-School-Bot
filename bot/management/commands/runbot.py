from django.core.management.base import BaseCommand
import asyncio
from bot.telegram_bot import main as run_telegram_bot

class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        try:
            asyncio.run(run_telegram_bot())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Bot stopped gracefully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running bot: {e}'))