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

# --- Database Selection (MySQL or SQLite) ---
# Set to 'mysql' or 'sqlite'
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

# MySQL Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "support_bot")
DB_PORT = os.getenv("DB_PORT", "3306")

# SQLite Database Configuration
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "bot_database.db")
