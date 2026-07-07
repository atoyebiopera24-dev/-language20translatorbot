import os
import logging
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

app = Flask(__name__)
translator = Translator()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN not set!")
    raise ValueError("TELEGRAM_TOKEN is required")

# ============= LANGUAGES =============
LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh-cn': 'Chinese (Simplified)', 'ar': 'Arabic',
    'hi': 'Hindi', 'bn': 'Bengali', 'ur': 'Urdu', 'tr': 'Turkish',
    'nl': 'Dutch', 'pl': 'Polish', 'vi': 'Vietnamese', 'th': 'Thai',
    'id': 'Indonesian', 'ms': 'Malay', 'sw': 'Swahili', 'ta': 'Tamil',
    'te': 'Telugu', 'mr': 'Marathi', 'gu': 'Gujarati', 'kn': 'Kannada',
    'ml': 'Malayalam', 'pa': 'Punjabi', 'af': 'Afrikaans', 'sq': 'Albanian',
    'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian',
    'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan', 'hr': 'Croatian',
    'cs': 'Czech', 'da': 'Danish', 'eo': 'Esperanto', 'et': 'Estonian',
    'tl': 'Filipino', 'fi': 'Finnish', 'gl': 'Galician', 'ka': 'Georgian',
    'el': 'Greek', 'ht': 'Haitian Creole', 'ha': 'Hausa', 'he': 'Hebrew',
    'hu': 'Hungarian', 'is': 'Icelandic', 'ig': 'Igbo', 'ga': 'Irish',
    'jw': 'Javanese', 'kk': 'Kazakh', 'km': 'Khmer', 'rw': 'Kinyarwanda',
    'ku': 'Kurdish', 'ky': 'Kyrgyz', 'lo': 'Lao', 'la': 'Latin',
    'lv': 'Latvian', 'lt': 'Lithuanian', 'lb': 'Luxembourgish', 'mk': 'Macedonian',
    'mg': 'Malagasy', 'mt': 'Maltese', 'mi': 'Maori', 'mn': 'Mongolian',
    'my': 'Myanmar', 'ne': 'Nepali', 'no': 'Norwegian', 'or': 'Odia',
    'ps': 'Pashto', 'fa': 'Persian', 'ro': 'Romanian', 'sm': 'Samoan',
    'gd': 'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho', 'sn': 'Shona',
    'sd': 'Sindhi', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian',
    'so': 'Somali', 'su': 'Sundanese', 'sv': 'Swedish', 'tg': 'Tajik',
    'tt': 'Tatar', 'tk': 'Turkmen', 'uk': 'Ukrainian', 'ug': 'Uyghur',
    'uz': 'Uzbek', 'cy': 'Welsh', 'xh': 'Xhosa', 'yi': 'Yiddish',
    'yo': 'Yoruba', 'zu': 'Zulu'
}

user_preferences = {}

# ============= COMMANDS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🌟 Hello {user.first_name}!\n\n"
        f"I'm Language Translator Bot.\n"
        f"Send me any text to translate!\n\n"
        f"Commands:\n"
        f"/start - Show this\n"
        f"/help - Help guide\n"
        f"/languages - All languages\n"
        f"/setlang - Set default language\n\n"
        f"Examples:\n"
        f'"Hello in Spanish"\n'
        f'"to French: Good morning"',
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📚 *How to use:*\n\n"
        f"1. Send text to translate\n"
        f"2. Use: 'to Spanish: Hello' or 'Hello in French'\n"
        f"3. Click buttons to change language\n\n"
        f"Commands:\n"
        f"/start - Welcome\n"
        f"/help - This help\n"
        f"/languages - All languages\n"
        f"/setlang - Set default",
        parse_mode='Markdown'
    )

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    langs = list(LANGUAGES.items())[:20]
    text = "🌍 *Languages:*\n\n"
    for code, name in langs:
        text += f"• {name} (`{code}`)\n"
    text += "\n...and 80+ more!"
    await update.message.reply_text(text, parse_mode='Markdown')

async def setlang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    sorted_langs = sorted(LANGUAGES.items())[:9]
    
    for i, (code, name) in enumerate(sorted_langs):
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(name[:12], callback_data=f"setlang_{code}"))
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📚 More", callback_data="more_langs")])
    
    await update.message.reply_text(
        "Select default language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang_code = query.data.replace("setlang_", "")
    lang_name = LANGUAGES.get(lang_code, lang_code)
    user_preferences[query.from_user.id] = lang_code
    
    await query.edit_message_text(f"✅ Default: {lang_name}")

async def more_langs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    sorted_langs = sorted(LANGUAGES.items())[9:18]
    
    for i, (code, name) in enumerate(sorted_langs):
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(name[:12], callback_data=f"setlang_{code}"))
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_langs")])
    
    await query.edit_message_text(
        "More languages:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_langs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    sorted_langs = sorted(LANGUAGES.items())[:9]
    
    for i, (code, name) in enumerate(sorted_langs):
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(name[:12], callback_data=f"setlang_{code}"))
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📚 More", callback_data="more_langs")])
    
    await query.edit_message_text(
        "Select default language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return
    
    text = update.message.text.strip()
    user_id = update.effective_user.id
    target_lang = user_preferences.get(user_id, 'en')
    
    # Parse inline commands
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
    
    try:
        detection = translator.detect(text_to_translate)
        source_lang = detection.lang
        source_name = LANGUAGES.get(source_lang, source_lang)
        target_name = LANGUAGES.get(target_lang, target_lang)
        
        result = translator.translate(text_to_translate, dest=target_lang)
        
        response = f"🌐 *Translation*\n\n"
        response += f"📝 *Original* ({source_name}):\n`{text_to_translate[:500]}`\n\n"
        response += f"🔤 *Translated* ({target_name}):\n`{result.text[:500]}`"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Change", callback_data="change_lang"),
                InlineKeyboardButton("💾 Set Default", callback_data=f"setdefault_{target_lang}")
            ]
        ]
        
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text(
            "❌ Translation failed. Try:\n"
            "• Shorter text\n"
            "• Different language\n"
            "• 'to Spanish: Hello' format"
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "change_lang":
        keyboard = []
        row = []
        sorted_langs = sorted(LANGUAGES.items())[:9]
        
        for i, (code, name) in enumerate(sorted_langs):
            if i % 3 == 0 and i > 0:
                keyboard.append(row)
                row = []
            row.append(InlineKeyboardButton(name[:12], callback_data=f"trans_{code}"))
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        await query.edit_message_text(
            "Select translation language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("trans_"):
        lang_code = data.replace("trans_", "")
        lang_name = LANGUAGES.get(lang_code, lang_code)
        await query.edit_message_text(
            f"✅ Set to {lang_name}\n\nSend text to translate!"
        )
    
    elif data.startswith("setdefault_"):
        lang_code = data.replace("setdefault_", "")
        lang_name = LANGUAGES.get(lang_code, lang_code)
        user_preferences[query.from_user.id] = lang_code
        await query.edit_message_text(f"✅ Default: {lang_name}")
    
    elif data == "cancel":
        await query.edit_message_text("❌ Cancelled")

def find_language_code(query):
    query = query.lower().strip()
    
    if query in LANGUAGES:
        return query
    
    for code, name in LANGUAGES.items():
        if query == name.lower():
            return code
        if query in name.lower() or name.lower() in query:
            return code
    
    return 'en'

# ============= FLASK APP =============

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("languages", languages_command))
application.add_handler(CommandHandler("setlang", setlang_command))

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))

application.add_handler(CallbackQueryHandler(set_language_callback, pattern="^setlang_"))
application.add_handler(CallbackQueryHandler(button_callback, pattern="^(change_lang|trans_|setdefault_|cancel)"))
application.add_handler(CallbackQueryHandler(more_langs_callback, pattern="^more_langs$"))
application.add_handler(CallbackQueryHandler(back_langs_callback, pattern="^back_langs$"))

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.process_update(update)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/')
def health():
    return 'Bot is running!', 200

if __name__ == '__main__':
    if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
        webhook_url = f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}/webhook"
        application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook: {webhook_url}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
