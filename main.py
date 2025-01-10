import logging
import os
import re
import socket
import unicodedata

from dotenv import load_dotenv
from httpcore import ConnectError
from telegram.ext import Application, CommandHandler, MessageHandler, filters

load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="logs.log",
    encoding="utf-8",
    filemode="a",
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Initiate the bot token as a variable. The token is stored in a .env file.
token = os.getenv("TOKEN_BOT")

PAM_CHAT_ID = os.getenv("PAM_CHAT_ID")


async def start(update, context):
    """Handle the /help command."""
    await update.message.reply_text(
        """Hello! Send your text and you'll get your text back in reverse!
"""
    )


async def boop(update, context):
    """Handle the /help command."""
    await update.message.reply_text(
        """This is definitely my bot ! @TechSherpa here!
"""
    )


import unicodedata


def reverse_text_sense_preserved(input_text):
    """
    Reverse the letters of each word while maintaining word order and punctuation.
    """

    def reverse_word(word):
        # Normalize the word to separate accents from base characters
        normalized = unicodedata.normalize("NFD", word)

        # Split the word into characters while preserving letters and apostrophes as a single unit
        letters = []
        others = []
        for char in normalized:
            if unicodedata.category(char).startswith("L") or char == "'":
                letters.append(
                    char
                )  # Treat letters and apostrophes as part of the word
            else:
                others.append(char)  # Non-letter characters are handled separately

        # Reverse the letters while keeping apostrophes intact
        reversed_letters = list(reversed(letters))
        result = []
        for char in word:
            if char in letters:
                result.append(reversed_letters.pop(0))  # Replace with reversed letters
            else:
                result.append(char)  # Keep other characters in place

        # Combine and normalize back to composed form
        return unicodedata.normalize("NFC", "".join(result))

    reversed_lines = []
    for line in input_text.splitlines():
        if line.strip():  # Process non-empty lines
            reversed_words = [reverse_word(word) for word in line.split()]
            reversed_lines.append(" ".join(reversed_words))
        else:
            reversed_lines.append("")  # Preserve empty lines

    return "\n".join(reversed_lines)


async def reverse_message(update, context):
    """Handle incoming messages and reply with the reversed text."""
    user_id = update.message.from_user.id

    # Check if the message has text, photo with caption, or video with caption
    if update.message.text:
        user_message = update.message.text
    elif update.message.caption:
        user_message = update.message.caption
    else:
        # If it's neither text nor an image/video with caption, ignore it
        return

    # If it's a direct message (DM) or from a specific chat, reverse the text
    if update.message.chat.type == "private" or str(user_id) == PAM_CHAT_ID:
        reversed_message = reverse_text_sense_preserved(user_message)

        if update.message.text:
            # Respond to a text message
            await update.message.reply_text(reversed_message)
        elif update.message.photo:
            # Respond to a photo with the reversed caption
            await update.message.reply_photo(
                photo=update.message.photo[-1].file_id, caption=reversed_message
            )
        elif update.message.video:
            # Respond to a video with the reversed caption
            await update.message.reply_video(
                video=update.message.video.file_id, caption=reversed_message
            )


def main():
    """Run the bot."""
    print("Starting bot...")
    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("boop", boop))

    # Message handler for reversing text
    application.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND,
            reverse_message,
        )
    )

    try:
        application.run_polling()
    except ConnectError as e:
        logger.error(f"Connection error: {e}")
    except socket.gaierror as e:
        logger.error(f"Hostname resolution error: {e}")


if __name__ == "__main__":
    main()
