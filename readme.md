
# Badminton Bot

  

This is a Telegram bot for managing badminton training sessions. It allows administrators to create and delete training sessions, while users can sign up for or cancel their registration. The bot keeps track of all participants and notifies admins about new registrations and cancellations.

## Installation

  

1. Clone the repository.

2. Install the required dependencies:

```bash

pip install -r requirements.txt

```

  

## Configuration

  

Create a `.env` file in the root of the project and add the following environment variables:

  

```
PUBLIC_CHAT_ID=-****************
PRIVATE_CHAT_ID=-****************
USER_BOT_API_KEY=**********:ABC*********************************
ADMIN_BOT_API_KEY==**********:ABC*********************************
ADMIN_USER_IDS=*********
BOT_USERNAME=yourBotUserName
```

  

### Environment Variables Explanation

  

*  `PUBLIC_CHAT_ID`: The ID of the public Telegram chat where training announcements are posted for all users.

*  `PRIVATE_CHAT_ID`: The ID of the private Telegram chat for admins and trainers, where more detailed information and notifications are sent.

*  `USER_BOT_API_KEY`: The Telegram Bot API token for the bot that regular users interact with.

*  `ADMIN_BOT_API_KEY`: The Telegram Bot API token for the bot that admins and trainers use for management tasks.

*  `ADMIN_USER_IDS`: A comma-separated list of Telegram user IDs for the administrators.

*  `BOT_USERNAME`: The username of the public-facing bot.

## Setup and Running the Bot

### Initial Setup

The initial setup and database migrations are handled automatically. When an administrator sends the `/start` command to the Admin Bot, it will trigger the necessary database migrations to ensure the environment is correctly configured.

### Running the Bot

You can run the bot in two ways:

#### 1. Using Docker

You can use Docker Compose to build and run the bots in isolated containers.

1.  **Build the image:**
    ```bash
    docker-compose build
    ```
2.  **Run the services:**
    ```bash
    docker-compose up
    ```

#### 2. Manually

Alternatively, you can run the bots directly from your terminal. You will need two separate terminal sessions for this, as `admin.py` and `user.py` are the entry points for the two different bots.

1.  **Run the Admin Bot:**
    In your first terminal session, start the Admin Bot:
    ```bash
    python admin.py
    ```

2.  **Run the User Bot:**
    In a second terminal session, start the User Bot:
    ```bash
    python user.py
    ```

## Architecture Overview

This project uses a two-bot, two-chat system to separate user-facing interactions from administrative tasks.

  

### Bots

  

1.  **User Bot (`USER_BOT_API_KEY`, `@BOT_USERNAME`)**: This is the public bot that regular users interact with to register for training sessions, view schedules, and receive general announcements.

  

2.  **Admin Bot (`ADMIN_BOT_API_KEY`)**: This bot is for administrators and trainers. It provides commands for managing events, viewing participant lists, and other administrative functions. This keeps the user-facing bot clean and simple.

  

### Chats

  

1.  **Public Chat (`PUBLIC_CHAT_ID`)**: This is the main channel where announcements about new training sessions are posted. Regular users can see these messages and use the User Bot to sign up.

  

2.  **Private Chat (`PRIVATE_CHAT_ID`)**: This is a restricted channel for admins and trainers. The Admin Bot posts more detailed logs and notifications here, such as when a user registers for a session, cancels, or when a session is full. This allows for easy monitoring and management without cluttering the public channel.

  

## Finding Telegram IDs

  

To configure the bot, you need the IDs for the public and private chats, as well as the user IDs for administrators. An easy way to find these is setup the bot to print the JSON data of messages the bot receives, then forward messages from specific chats, bots and users.  
By inspecting the message data your bot receives, you can easily find all the necessary IDs for the environment variables.
