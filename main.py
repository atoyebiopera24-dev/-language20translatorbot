import os
import logging
import json
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from googletrans import Translator
import re

# ============= CONFIGURATION =============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize translator
translator = Translator()

# Get bot token from environment variable
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN not set in environment variables!")
    raise ValueError("TELEGRAM_TOKEN is required")

# ============= LANGUAGE SUPPORT =============
LANGUAGES = {
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'am': 'Amharic',
    'ar': 'Arabic',
    'hy': 'Armenian',
    'az': 'Azerbaijani',
    'eu': 'Basque',
    'be': 'Belarusian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'ny': 'Chichewa',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'co': 'Corsican',
    'hr': 'Croatian',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'en': 'English',
    'eo': 'Esperanto',
    'et': 'Estonian',
    'tl': 'Filipino',
    'fi': 'Finnish',
    'fr': 'French',
    'fy': 'Frisian',
    'gl': 'Galician',
    'ka': 'Georgian',
    'de': 'German',
    'el': 'Greek',
    'gu': 'Gujarati',
    'ht': 'Haitian Creole',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'he': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hu': 'Hungarian',
    'is': 'Icelandic',
    'ig': 'Igbo',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'jw': 'Javanese',
    'kn': 'Kannada',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'rw': 'Kinyarwanda',
    'ko': 'Korean',
    'ku': 'Kurdish',
    'ky': 'Kyrgyz',
    'lo': 'Lao',
    'la': 'Latin',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'lb': 'Luxembourgish',
    'mk': 'Macedonian',
    'mg': 'Malagasy',
    'ms': 'Malay',
    'ml': 'Malayalam',
    'mt': 'Maltese',
    'mi': 'Maori',
    'mr': 'Marathi',
    'mn': 'Mongolian',
    'my': 'Myanmar (Burmese)',
    'ne': 'Nepali',
    'no': 'Norwegian',
    'or': 'Odia (Oriya)',
    'ps': 'Pashto',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'pa': 'Punjabi',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sm': 'Samoan',
    'gd': 'Scots Gaelic',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'sn': 'Shona',
    'sd': 'Sindhi',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'es': 'Spanish',
    'su': 'Sundanese',
    'sw': 'Swahili',
    'sv': 'Swedish',
    'tg': 'Tajik',
    'ta': 'Tamil',
    'tt': 'Tatar',
    'te': 'Telugu',
    'th': 'Thai',
    'tr': 'Turkish',
    'tk': 'Turkmen',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'ug': 'Uyghur',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'cy': 'Welsh',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zu': 'Zulu'
}

# In-memory storage for user preferences (for production, use a database)
user_preferences = {}

# ============= COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    welcome_message = f"""
🌟 *Welcome to Language Translator Bot!* 🌟

Hello {user.first_name}! I'm your personal translation assistant powered by AI.

✨ *Features:*
• Auto-detect source language
• Translate to 100+ languages
• Quick language selection buttons
• Save your default language

📝 *How to use:*
1. Send me any text
2. Click a language button to translate
3. Or use: `"to Spanish: Hello"` or `"Hello in French"`

🔧 *Commands:*
/start - Show this message
/help - Detailed instructions
/languages - View all supported languages
/setlang - Set your default language

Let's start translating! Send me something to translate. 🚀
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
📚 *Language Translator Bot - Help Guide*

🔹 *Basic Usage:*
Simply send any text message and I'll translate it!

🔹 *Quick Translation Format:*
• `"to Spanish: Hello world"` - Translate to Spanish
• `"Bonjour in English"` - Translate to English
• `"to Japanese: I love programming"`

🔹 *Interactive Buttons:*
After translation, click:
• "Change Language" - Choose a different language
• "Set Default" - Save as your default language

🔹 *Commands:*
/start - Welcome message
/help - This help guide
/languages - Show all supported languages
/setlang - Set your default translation language

🔹 *Tips:*
• I automatically detect the source language!
• Your default language is saved for future translations
• I support 100+ languages worldwide

💡 *Examples:*
• `"to French: How are you?"`
• `"I love coding in German"`
• Just send: `"Hello"` and click a button!

Need more help? Just ask! 😊
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /languages command."""
    # Show first 20 languages
    lang_list = []
    for i, (code, name) in enumerate(sorted(LANGUAGES.items())):
        if i < 20:
            lang_list.append(f"• {name} (`{code}`)")
    
    lang_text = "🌍 *Supported Languages (Partial List):*\n\n" + "\n".join(lang_list) + "\n\n...and 80+ more languages!\n\nUse /setlang to see more options."
    await update.message.reply_text(lang_text, parse_mode='Markdown')

async def setlang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setlang command to set default language."""
    keyboard = []
    row = []
    sorted_langs = sorted(LANGUAGES.items())
    
    for i, (code, name) in enumerate(sorted_langs[:12]):  # Show first 12
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(name[:15], callback_data=f"setlang_{code}"))
    if row:
        keyboard.append(row)
    
    # Add "More Languages" button
    keyboard.append([InlineKeyboardButton("📚 More Languages", callback_data="more_languages")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌐 *Select your default translation language:*\n\nChoose from popular languages below or click 'More Languages' for the full list.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def more_languages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show more languages when user clicks 'More Languages'."""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    sorted_langs = sorted(LANGUAGES.items())
    
    for i, (code, name) in enumerate(sorted_langs[12:24]):  # Next 12
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(name[:15], callback_data=f"setlang_{code}"))
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_languages")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🌐 *More Languages:*\n\nSelect your default translation language:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def back_to_languages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Go back to main language selection."""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    sorted_langs = sorted(LANGUAGES.items())
    
    for i, (code, name) in enumerate(sorted_langs[:12]):
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(name[:15], callback_data=f"setlang_{code}"))
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📚 More Languages", callback_data="more_languages")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🌐 *Select your default translation language:*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection from callback."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.replace("setlang_", "")
    lang_name = LANGUAGES.get(lang_code, lang_code)
    
    user_preferences[user_id] = lang_code
    
    await query.edit_message_text(
        f"✅ *Default language set to:* {lang_name}\n\n"
        f"Now send me any text and I'll translate it to {lang_name}!",
        parse_mode='Markdown'
    )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text translation."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    user_id = update.effective_user.id
    target_lang = user_preferences.get(user_id, 'en')  # Default to English
    
    # Check for inline translation format: "to Spanish: Hello" or "Hello in French"
    match_to = re.search(r'^to\s+([a-zA-Z\s\-]+)\s*:\s*(.+)$', text, re.IGNORECASE)
    match_in = re.search(r'^(.+?)\s+in\s+([a-zA-Z\s\-]+)$', text, re.IGNORECASE)
    
    if match_to:
        lang_query = match_to.group(1).strip()
        text_to_translate = match_to.group(2).strip()
        target_lang = find_language_code(lang_query)
    elif match_in:
        text_to_translate = match_in.group(1).strip()
        lang_query = match_in.group(2).strip()
        target_lang = find_language_code(lang_query)
    else:
        text_to_translate = text
    
    # Show typing indicator
    await update.message.chat.send_action(action="typing")
    
    try:
        # Detect source language
        detection = translator.detect(text_to_translate)
        source_lang = detection.lang
        
        # Get language names
        source_lang_name = LANGUAGES.get(source_lang, source_lang)
        target_lang_name = LANGUAGES.get(target_lang, target_lang)
        
        # Translate
        result = translator.translate(text_to_translate, dest=target_lang)
        
        # Create response
        response = f"""
🌐 *Translation Result*

📝 *Original* ({source_lang_name}):
`{text_to_translate}`

🔤 *Translated* ({target_lang_name}):
`{result.text}`

📊 *Confidence*: {detection.confidence:.1%}
"""
        
        # Create inline keyboard for further actions
        keyboard = [
            [
                InlineKeyboardButton("🔄 Change Language", callback_data="change_lang"),
                InlineKeyboardButton("💾 Set as Default", callback_data=f"setdefault_{target_lang}")
            ],
            [
                InlineKeyboardButton("📋 Copy Result", callback_data=f"copy_{result.text[:50]}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text(
            "❌ *Translation Error*\n\n"
            "I couldn't translate that text. Please check:\n"
            "• The text isn't too long (max 5000 characters)\n"
            "• The language is supported\n"
            "• Try a different language\n\n"
            f"Error: {str(e)[:100]}",
            parse_mode='Markdown'
        )

# ============= CALLBACK HANDLERS =============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "change_lang":
        # Show language selection for translation
        keyboard = []
        row = []
        sorted_langs = sorted(LANGUAGES.items())
        
        for i, (code, name) in enumerate(sorted_langs[:12]):
            if i % 3 == 0 and i > 0:
                keyboard.append(row)
                row = []
            row.append(InlineKeyboardButton(name[:15], callback_data=f"trans_lang_{code}"))
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("📚 More Languages", callback_data="more_trans_langs")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_trans")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌐 *Select translation language:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "more_trans_langs":
        # Show more translation languages
        keyboard = []
        row = []
        sorted_langs = sorted(LANGUAGES.items())
        
        for i, (code, name) in enumerate(sorted_langs[12:24]):
            if i % 3 == 0 and i > 0:
                keyboard.append(row)
                row = []
            row.append(InlineKeyboardButton(name[:15], callback_data=f"trans_lang_{code}"))
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="change_lang")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌐 *More translation languages:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("trans_lang_"):
        lang_code = data.replace("trans_lang_", "")
        lang_name = LANGUAGES.get(lang_code, lang_code)
        
        # Store in context for later use
        context.user_data['target_lang'] = lang_code
        
        await query.edit_message_text(
            f"✅ *Language set to:* {lang_name}\n\n"
            f"Now send me the text you want to translate to {lang_name}!\n"
            f"Or use the format: `'to {lang_name}: your text'`",
            parse_mode='Markdown'
        )
    
    elif data == "cancel_trans":
        await query.edit_message_text("❌ Translation cancelled. Send me text to translate!")
    
    elif data.startswith("setdefault_"):
        lang_code = data.replace("setdefault_", "")
        lang_name = LANGUAGES.get(lang_code, lang_code)
        user_preferences[user_id] = lang_code
        
        await query.edit_message_text(
            f"✅ *Default language set to:* {lang_name}\n\n"
            f"All future translations will use {lang_name} unless you specify otherwise.",
            parse_mode='Markdown'
        )
    
    elif data.startswith("copy_"):
        # Just acknowledge the copy request
        await query.edit_message_text(
            "📋 *Text to copy:*\n\n"
            f"`{data.replace('copy_', '')}`",
            parse_mode='Markdown'
        )

# ============= HELPER FUNCTIONS =============

def find_language_code(lang_query: str) -> str:
    """Find language code from language name or code."""
    lang_query = lang_query.lower().strip()
    
    # Check if it's already a code
    if lang_query in LANGUAGES:
        return lang_query
    
    # Check if it matches a language name (case-insensitive)
    for code, name in LANGUAGES.items():
        if lang_query == name.lower():
            return code
        # Partial match
        if lang_query in name.lower() or name.lower() in lang_query:
            return code
    
    # Try to find by first few letters
    for code, name in LANGUAGES.items():
        if name.lower().startswith(lang_query[:3]):
            return code
    
    return 'en'  # Default to English if not found

# ============= FLASK WEBHOOK =============

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates via webhook."""
    try:
        # Get the update data
        update_data = request.get_json(force=True)
        logger.info(f"Received update: {json.dumps(update_data)[:200]}")
        
        # Create Update object and process
        update = Update.de_json(update_data, application.bot)
        application.process_update(update)
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def health_check():
    """Health check endpoint for Railway."""
    return jsonify({
        'status': 'running',
        'bot': 'Language Translator Bot',
        'username': '@language20translatorbot'
    }), 200

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """Manually set the webhook URL."""
    try:
        webhook_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
        if not webhook_url:
            return jsonify({'error': 'RAILWAY_PUBLIC_DOMAIN not set'}), 400
        
        webhook_url = f"https://{webhook_url}/webhook"
        result = application.bot.set_webhook(webhook_url)
        
        return jsonify({
            'status': 'success',
            'webhook_url': webhook_url,
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"Set webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# ============= MAIN =============

# Initialize the Telegram application
application = Application.builder().token(TOKEN).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("languages", languages_command))
application.add_handler(CommandHandler("setlang", setlang_command))

# Message handler for text
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))

# Callback handlers
application.add_handler(CallbackQueryHandler(set_language_callback, pattern="^setlang_"))
application.add_handler(CallbackQueryHandler(button_callback, pattern="^(change_lang|more_trans_langs|trans_lang_|setdefault_|copy_|cancel_trans)"))
application.add_handler(CallbackQueryHandler(more_languages_callback, pattern="^more_languages$"))
application.add_handler(CallbackQueryHandler(back_to_languages_callback, pattern="^back_to_languages$"))

if __name__ == '__main__':
    # Set webhook if running on Railway
    if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
        webhook_url = f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}/webhook"
        application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
