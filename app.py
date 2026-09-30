import os
import threading
from flask import Flask
from support_bot import main as bot_main  # غيّر الاسم حسب ملف البوت

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

@app.route("/health")
def health():
    return "OK", 200

def run_bot():
    import asyncio
    asyncio.run(bot_main())

if __name__ == "__main__":
    # شغّل البوت في خيط منفصل
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # شغّل خادم الويب على المنفذ يلي Render بيعطيه
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
