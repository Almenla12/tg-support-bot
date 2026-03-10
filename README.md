# Telegram Support Bot (Forum/Topics based)

A lightweight and efficient Telegram Support Bot built with `aiogram 3.x`. It uses Telegram's **Forum (Topics)** feature to organize support tickets. Each user who contacts the bot gets their own dedicated topic in your support group.

## Features

-   **Topic-based Tickets:** Every user gets a unique topic in a Telegram Forum group.
-   **Bi-directional Communication:** Support agents reply directly in the topic, and the message is forwarded to the user.
-   **Edit Support:** When a user edits their message, the bot notifies the support group and forwards the updated content.
-   **MySQL Persistence:** Remembers the mapping between users and topics.

## Prerequisites

-   Python 3.9+
-   MySQL Database
-   A Telegram Bot token (from [@BotFather](https://t.me/BotFather))
-   A Telegram Group with **Topics** enabled.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/tg-support-bot.git
    cd tg-support-bot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the bot:**
    -   Copy `.env.example` to `.env`.
    -   Fill in your `BOT_TOKEN`, `GROUP_ID`, and database credentials.
    -   `GROUP_ID` is the ID of your support group (where topics will be created).

4.  **Run the bot:**
    ```bash
    python support_bot.py
    ```

## Usage

1.  Users send a private message to the bot.
2.  The bot creates a new topic in the designated support group.
3.  Support agents reply to the user by sending a message inside that topic.
4.  The bot forwards the reply to the user.

## License

MIT
