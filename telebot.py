from dotenv import load_dotenv

load_dotenv()

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from LLM import process_location_setup, process_text_message
from tts import tts
import os


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when /start is issued."""
    await update.message.reply_text(
        "Hi! Use /location to share your location, then /weather to get the weather."
    )


async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /location command - request user's location."""
    await update.message.reply_text(
        "Please share your location.",
        reply_markup=__import__('telegram').ReplyKeyboardMarkup(
            [[__import__('telegram').KeyboardButton(text="📍 Share Location", request_location=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when user shares their location."""
    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude
    context.user_data["location"] = {
        "latitude": latitude,
        "longitude": longitude,
    }
    
    await update.message.reply_text(
        process_location_setup(latitude, longitude, str(update.effective_user.id))
    )


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get weather for the user's shared location."""
    location = context.user_data.get("location")
    if not location:
        await update.message.reply_text("Please use /location and share your location first.")
        return

    response = process_text_message(
        "What is the weather at my saved location?",
        str(update.effective_user.id),
        location,
    )
    audio_path = tts(response, lang="hi-IN")
    try:
        with open(audio_path, "rb") as audio_file:
            await update.message.reply_audio(audio=audio_file)
    finally:
        os.remove(audio_path)


async def post_init(application: Application) -> None:
    """Set bot commands that appear in the / menu."""
    commands = [
        BotCommand("start", "Show bot introduction"),
        BotCommand("location", "Share your location and get coordinates"),
        BotCommand("weather", "Get weather at your shared location"),
    ]
    await application.bot.set_my_commands(commands)


def main() -> None:
    """Start the bot."""
    # Replace with your token from BotFather
    TOKEN = "8676349485:AAGI9ZsjQ4VxEYX3TR-kUI1Ov9-93tvSE2Q"
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    application.post_init = post_init

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("location", location_command))
    application.add_handler(CommandHandler("weather", weather_command))
    
    # Register message handlers
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()