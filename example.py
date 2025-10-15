import hashlib
from datetime import datetime, timedelta
import telebot

TOKEN = "8328320340:AAH1HJo8VfpxqXOPc_mJ97s15FSUahcs8WU"
bot = telebot.TeleBot(TOKEN)

def generate_adb_password(vin, custom_time=None, use_previous_interval=False):
    interval_ms = 600000
    if custom_time:
        dt = datetime.strptime(custom_time, "%Y-%m-%d %H:%M")
        current_time = int(dt.timestamp() * 1000)
    else:
        current_time = int(datetime.now().timestamp() * 1000)
    if use_previous_interval:
        current_time -= interval_ms
    if len(vin) < 6:
        return "error: vin length < 6"
    vin_suffix = vin[-6:]
    time_interval = current_time // interval_ms
    base_string = f"{vin_suffix}&&{time_interval}#"
    sha256_hash = hashlib.sha256(base_string.encode("utf-8")).hexdigest().upper()
    md5_hash = hashlib.md5(sha256_hash.encode("utf-8")).hexdigest()
    return md5_hash[-6:] if len(md5_hash) >= 6 else md5_hash

def get_passwords_for_time(vin, custom_time):
    return {
        "custom_time": custom_time,
        "passwords": [
            generate_adb_password(vin, custom_time),
            generate_adb_password(vin, custom_time, use_previous_interval=True)
        ],
        "time_info": {
            "current_interval_start": datetime.strptime(custom_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S"),
            "previous_interval_start": (
                datetime.strptime(custom_time, "%Y-%m-%d %H:%M") - timedelta(minutes=10)
            ).strftime("%Y-%m-%d %H:%M:%S")
        }
    }

user_state = {}

@bot.message_handler(commands=['start', 'reset'])
def start_handler(message):
    user_state.pop(message.chat.id, None)
    bot.reply_to(message, "Привет! 🚗 Отправь VIN (минимум 6 символов).")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    cid = message.chat.id
    text = message.text.strip()

    if cid not in user_state:
        if len(text) < 6:
            bot.reply_to(message, "❌ VIN должен содержать минимум 6 символов.")
            return
        user_state[cid] = {'vin': text}
        bot.reply_to(message, "✅ VIN сохранён! Теперь отправь время (ГГГГ-ММ-ДД ЧЧ:ММ):")
    else:
        vin = user_state[cid]['vin']
        try:
            result = get_passwords_for_time(vin, text)
            msg = (
                f"🔹 VIN: {vin}\n"
                f"🕒 Время: {result['custom_time']}\n\n"
                f"Текущий интервал: {result['time_info']['current_interval_start']}\n"
                f"Предыдущий интервал: {result['time_info']['previous_interval_start']}\n\n"
                f"🔐 Пароли:\n"
                f"1️⃣ {result['passwords'][0]}\n"
                f"2️⃣ {result['passwords'][1]}"
            )
            bot.reply_to(message, msg)
        except Exception:
            bot.reply_to(message, "❌ Ошибка формата времени! Используй ГГГГ-ММ-ДД ЧЧ:ММ")

print("Bot is running...")
bot.infinity_polling()
