# config.py
# Configuration file for Telegram Support Bot
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Telegram Bot Credentials ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID of your support group (where tickets will be sent)
# Note: Usually starts with a hyphen "-"
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

# List of bot administrators (comma-separated user IDs)
ADMIN_USERS_LIST = os.getenv("ADMIN_USERS_LIST", "")
ADMIN_USERS = {int(uid.strip()) for uid in ADMIN_USERS_LIST.split(',') if uid.strip().isdigit()}

# --- MySQL Database (Primary bot database) ---
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
