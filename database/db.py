# database/db.py
import asyncio
import logging
import ssl
from contextlib import asynccontextmanager

import aiomysql
import aiosqlite
import config

# Global variables for database pools
db_pool = None

@asynccontextmanager
async def get_db_connection():
    """Provides an asynchronous database connection (MySQL or SQLite)."""
    if config.DB_TYPE == "mysql":
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                yield cursor
    else:  # SQLite
        async with aiosqlite.connect(config.SQLITE_DB_PATH) as conn:
            async with conn.cursor() as cursor:
                yield cursor
                await conn.commit()

async def initialize_db():
    """Initializes the database connection (pool for MySQL, file for SQLite)."""
    global db_pool
    try:
        if config.DB_TYPE == "mysql":
            # Create SSL context for Aiven
            ssl_context = ssl.create_default_context(cafile="ca.pem")
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            db_pool = await aiomysql.create_pool(
                host=config.DB_HOST,
                port=int(config.DB_PORT),
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                db=config.DB_NAME,
                ssl=ssl_context,
                autocommit=True,
                loop=asyncio.get_running_loop()
            )
            logging.info("Main MySQL connection pool created successfully.")
        else:
            logging.info(f"Using SQLite database at {config.SQLITE_DB_PATH}")
        
        # Initialize tables
        async with get_db_connection() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_topics (
                    user_id BIGINT PRIMARY KEY, 
                    topic_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logging.info("Check/Creation of 'user_topics' table completed.")
        return True
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}")
        return False

async def get_topic_id_for_user(user_id: int) -> int | None:
    async with get_db_connection() as cursor:
        query = "SELECT topic_id FROM user_topics WHERE user_id = %s" if config.DB_TYPE == "mysql" else "SELECT topic_id FROM user_topics WHERE user_id = ?"
        await cursor.execute(query, (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_user_id_for_topic(topic_id: int) -> int | None:
    async with get_db_connection() as cursor:
        query = "SELECT user_id FROM user_topics WHERE topic_id = %s" if config.DB_TYPE == "mysql" else "SELECT user_id FROM user_topics WHERE topic_id = ?"
        await cursor.execute(query, (topic_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def save_user_topic_mapping(user_id: int, topic_id: int) -> bool:
    async with get_db_connection() as cursor:
        try:
            if config.DB_TYPE == "mysql":
                query = "INSERT INTO user_topics (user_id, topic_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE topic_id = VALUES(topic_id);"
                await cursor.execute(query, (user_id, topic_id))
            else:
                query = "INSERT OR REPLACE INTO user_topics (user_id, topic_id, created_at, last_updated) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);"
                await cursor.execute(query, (user_id, topic_id))
            
            logging.info(f"DB: Link user_id {user_id} -> topic_id {topic_id} saved/updated.")
            return True
        except Exception as e:
            logging.error(f"DB Error: save_user_topic_mapping({user_id}, {topic_id}): {e}")
            return False

async def close_db():
    """Closes the database pool (for MySQL)."""
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
