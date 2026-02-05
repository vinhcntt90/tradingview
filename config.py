import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Security / Credentials
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_IDS = [
        chat_id.strip() 
        for chat_id in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") 
        if chat_id.strip()
    ]
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", os.path.join(BASE_DIR, "output"))
    
    # Charting
    DEFAULT_TIMEFRAME = "15m"
    LIMIT = 1000

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            print("[!] Warning: TELEGRAM_BOT_TOKEN not found in .env")
        if not cls.TELEGRAM_CHAT_IDS:
            print("[!] Warning: TELEGRAM_CHAT_IDS not found in .env")
        
        # Ensure output directory exists
        if not os.path.exists(cls.ARTIFACTS_DIR):
            os.makedirs(cls.ARTIFACTS_DIR)

# Auto-validate on import
Config.validate()
