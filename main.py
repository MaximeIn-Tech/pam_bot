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
    "t’nod": "don't",
    "t’ndid": "didn't",
    "t’nsi": "isn't",
    "tn’si": "isn't",
    "t’nasw": "wasn't",
    "t’nera": "aren't",
    "tn’seod": "doesn't",
    "t’nseod": "doesn't",
    "ev’uoy": "you've",
    "t'nac": "can't",
    "t'now": "won't",
    "t'nod": "don't",
    "t'ndid": "didn't",
    "t'nsi": "isn't",
    "tn'si": "isn't",
    "t'nasw": "wasn't",
    "t'nera": "aren't",
    "tn'seod": "doesn't",
    "t'nseod": "doesn't",
    "ev'uoy": "you've",
    # Add more contractions as needed
}


def reverse_text_sense_preserved(input_text):
    """
    Reverses a reversed text back to its original form while handling contractions properly.
    """

    def reverse_word(word):
        # Check if the word is a URL
        if re.match(r"https?://\S+", word):
            return word  # Return the URL as is, without reversing

        # Special cases: Don't reverse "am", "pm"
        if word.lower() in ["am", "pm"]:
            return word

        # Log to check how "1st" and similar words are handled
        logger.info(f"Processing word: {word}")

        # Handle ordinals like 1st, 2nd, 3rd, 10th, etc.
        ordinal_match = re.match(r"^(\D*)(\d+)(st|nd|rd|th)(\D*)$", word.lower())
        if ordinal_match:
            prefix = ordinal_match.group(1)
            number = ordinal_match.group(2)
            suffix = ordinal_match.group(3)
            suffix_end = ordinal_match.group(4)
            return prefix + number + suffix + suffix_end

        # Handling time (e.g., "12:30pm", "11:45am")
        if re.match(r"\d{1,2}:\d{2}(am|pm)", word.lower()):
            time, meridiem = word[:-2], word[-2:]
            return time + meridiem.lower()

        # Handling contractions (if applicable)
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
        reversed_letters = letters[::-1]  # Reverse the list of letters

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

    original_lines = []
    for line in input_text.splitlines():
        if line.strip():
            original_words = [reverse_word(word) for word in line.split()]
            logger.info(f"Reversed line: {' '.join(original_words)}")
            original_lines.append(" ".join(original_words))
        else:
            original_lines.append("")  # Preserve empty lines
    return "\n".join(original_lines)


async def reverse_message(update, context):
    """Handle incoming messages and reply with the reversed text."""
    message = update.message
    user_id = message.from_user.id
    chat_type = message.chat.type

    # Extraire le contenu texte pertinent (texte ou caption)
    user_message = message.text or message.caption
    if not user_message:
        return  # Rien à faire si aucun texte à inverser

    # Filtrer : accepter seulement les messages privés ou d'un chat spécifique
    if chat_type != "private" and str(user_id) != PAM_CHAT_ID:
        return

        # Cas spécial : animation + texte sans caption (ex: GIF depuis galerie Telegram)
    if message.animation and message.text and not message.caption:
        reversed_message = reverse_text_sense_preserved(message.text)
        await message.reply_animation(
            animation=message.animation.file_id, caption=reversed_message
        )
        return

    # Appliquer la fonction de reverse
    reversed_message = reverse_text_sense_preserved(user_message)

    # Dictionnaire de correspondance entre type de contenu et méthode de réponse
    reply_methods = {
        "text": lambda: message.reply_text(reversed_message),
        "photo": lambda: message.reply_photo(
            photo=message.photo[-1].file_id, caption=reversed_message
        ),
        "video": lambda: message.reply_video(
            video=message.video.file_id, caption=reversed_message
        ),
        "voice": lambda: message.reply_voice(
            voice=message.voice.file_id, caption=reversed_message
        ),
        "animation": lambda: message.reply_animation(
            animation=message.animation.file_id, caption=reversed_message
        ),
    }

    # Exécuter la bonne méthode de réponse selon le type de contenu
    for media_type, reply_func in reply_methods.items():
        if getattr(message, media_type, None):
            await reply_func()
            break  # Une seule réponse suffit


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
            (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE)
            & ~filters.COMMAND,
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
