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

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Initiate the bot token and chat_id as a variable. The token is stored in a .env file.
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


# Define the contraction map (you can extend this list as needed)
contractions_map = {
    "t’nac": "can't",
    "t’now": "won't",
    "t'nod": "don't",
    "t'ndid": "didn't",
    "t'nsi": "isn't",
    "t'nasw": "wasn't",
    "t'nera": "aren't",
    # Add more contractions as needed
}


def reverse_text_sense_preserved(input_text):
    """
    Reverses a reversed text back to its original form while handling contractions properly.
    """

    def reverse_word(word):
        # Special cases
        if word.lower() in ["am", "pm"]:
            return word
        if re.match(r"\d{1,2}:\d{2}(am|pm)", word.lower()):
            time, meridiem = word[:-2], word[-2:]
            return time + meridiem.lower()
        if word.lower() in contractions_map:
            return contractions_map[word.lower()]
        # Normalize the word to separate accents from base characters
        normalized = unicodedata.normalize("NFD", word)

        # Separate letters/apostrophes from non-letter characters
        letters = []
        others = []
        for char in normalized:
            if char.isalpha() or char == "'":
                letters.append(char)
            else:
                others.append(char)

        # Reverse letters without handling contractions
        reversed_letters = []
        i = len(letters) - 1

        while i >= 0:
            # Simply append the letter and move to the previous one
            reversed_letters.append(letters[i])
            i -= 1

        # Reconstruct the word by combining reversed letters and preserved punctuation
        result = []
        letter_index = 0
        other_index = 0
        for char in word:
            if char.isalpha() or char == "'":
                result.append(reversed_letters[letter_index])
                letter_index += 1
            else:
                result.append(others[other_index])
                other_index += 1

        # Normalize back to NFC to compose accented characters
        return unicodedata.normalize("NFC", "".join(result))

    # Process each line of the input text
    original_lines = []
    for line in input_text.splitlines():
        if line.strip():  # Process non-empty lines
            original_words = [reverse_word(word) for word in line.split()]
            original_lines.append(" ".join(original_words))
        else:
            original_lines.append("")  # Preserve empty lines

    return "\n".join(original_lines)


async def reverse_message(update, context):
    """Handle incoming messages and reply with the reversed text."""
    user_id = update.message.from_user.id

    # Check if the message has text, photo with caption, or video with caption
    if update.message.text:
        user_message = update.message.text
    elif update.message.caption:
        user_message = update.message.caption
    else:
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
