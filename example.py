import hashlib
from datetime import datetime, timedelta
import telebot

TOKEN = "8397224957:AAEKkBLFe101QNElIoLkwhg05dHnbmateD4"
bot = telebot.TeleBot(TOKEN)

login = "leo_zzz"
password = "uniz12345"

# хранение статуса пользователя
user_state = {}

# -----------------------------
# Генерация пароля (твоя логика)
# -----------------------------
def generate_adb_password(vin, custom_time=None, use_previous_interval=False):
    interval_ms = 600000  # 10 минут
    if custom_time:
        dt = datetime.strptime(custom_time, "%Y-%m-%d %H:%M")
        current_time = int(dt.timestamp() * 1000)
    else:
        current_time = int(datetime.now().timestamp() * 1000)

    if use_previous_interval:
        current_time += interval_ms

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
                datetime.strptime(custom_time, "%Y-%m-%d %H:%M") + timedelta(minutes=10)
            ).strftime("%Y-%m-%d %H:%M:%S")
        }
    }

# -----------------------------
# Авторизация
# -----------------------------
@bot.message_handler(commands=['start', 'reset'])
def start_handler(message):
    user_id = message.from_user.id
    user_state[user_id] = "awaiting_login"
    bot.reply_to(message, "Введите ваш логин:")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Шаг 1 — логин
    if user_id in user_state and user_state[user_id] == "awaiting_login":
        if text == login:
            user_state[user_id] = "awaiting_password"
            bot.reply_to(message, "✅ Логин верный.\nТеперь введите пароль:")
        else:
            bot.reply_to(message, "❌ Неверный логин. Попробуйте снова.")
        return

    # Шаг 2 — пароль
    if user_id in user_state and user_state[user_id] == "awaiting_password":
        if text == password:
            user_state[user_id] = "authorized"
            bot.reply_to(message, "✅ Авторизация успешна!\nТеперь отправьте VIN (минимум 6 символов).")
        else:
            bot.reply_to(message, "❌ Неверный пароль. Попробуйте снова.")
        return

    # Шаг 3 — после входа
    if user_id not in user_state or user_state[user_id] != "authorized":
        bot.reply_to(message, "Сначала введите /start и авторизуйтесь.")
        return

    # Если авторизован → VIN
    vin = text
    if len(vin) < 6:
        bot.reply_to(message, "❌ VIN должен содержать минимум 6 символов.")
        return

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        result = get_passwords_for_time(vin, current_time)
        msg = (
            f"🔹 VIN: {vin}\n"
            f"🕒 Время: {result['custom_time']}\n\n"
            f"Текущий интервал: {result['time_info']['current_interval_start']}\n"
            f"Следующий интервал: {result['time_info']['previous_interval_start']}\n\n"
            f"🔐 Пароли:\n"

        )
        bot.reply_to(message, msg)
        bot.reply_to(f"1️⃣ {result['passwords'][0]}", msg)


    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


print("Bot is running...")
bot.infinity_polling()
