import time
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8740554601:AAGB4AbrvPSYMd5dZTASkfvX2d3h23gV1QA"
ADMIN_ID = 1896626491
MANAGER_IDS = [1896626491]

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

ticket_counter = 0

# ================== АНТИСПАМ ==================

user_last_message = {}
user_last_ticket = {}

MESSAGE_COOLDOWN = 2
TICKET_COOLDOWN = 180


def is_spam(user_id):
    now = time.time()
    last = user_last_message.get(user_id, 0)
    if now - last < MESSAGE_COOLDOWN:
        return True
    user_last_message[user_id] = now
    return False


def ticket_cooldown(user_id):
    now = time.time()
    last = user_last_ticket.get(user_id, 0)
    if now - last < TICKET_COOLDOWN:
        return int(TICKET_COOLDOWN - (now - last))
    user_last_ticket[user_id] = now
    return 0


def contains_links(text):
    blocked = ["http", "https", "t.me", "www.", ".com", "@"]
    return any(word in text.lower() for word in blocked)


# ================== ПЕРЕВОДЫ ==================

translations = {
    "ru": {
        "menu": "🍽 Меню",
        "sales": "🎁 Акции",
        "problem": "🚫 Проблема",
        "suggestion": "💡 Предложение",
        "cancel": "❌ Отмена",
        "choose_day": "Выберите день недели:",
        "no_sales": "😢 Акций сейчас нет.",
        "write_problem": "Опишите проблему. Фото можно прикрепить 📷",
        "write_suggestion": "Напишите предложение. Фото можно прикрепить 📷",
        "ticket_sent": "✅ Заявка отправлена!",
        "cooldown": "⏳ Подождите {} сек.",
        "spam": "⚠ Не так быстро.",
        "too_long": "⚠ До 1000 символов.",
        "links_blocked": "🚫 Ссылки запрещены.",
        "cancelled": "❌ Действие отменено.",
        "main_menu": "Главное меню:"
    },
    "en": {
        "menu": "🍽 Menu",
        "sales": "🎁 Promotions",
        "problem": "🚫 Problem",
        "suggestion": "💡 Suggestion",
        "cancel": "❌ Cancel",
        "choose_day": "Choose a day:",
        "no_sales": "😢 No promotions now.",
        "write_problem": "Describe the problem. Photo optional 📷",
        "write_suggestion": "Write your suggestion. Photo optional 📷",
        "ticket_sent": "✅ Ticket sent!",
        "cooldown": "⏳ Wait {} sec.",
        "spam": "⚠ Too fast.",
        "too_long": "⚠ Max 1000 characters.",
        "links_blocked": "🚫 Links are not allowed.",
        "cancelled": "❌ Action cancelled.",
        "main_menu": "Main menu:"
    }
}

days = {
    "ru": {
        "Понедельник": "Monday",
        "Вторник": "Tuesday",
        "Среда": "Wednesday",
        "Четверг": "Thursday",
        "Пятница": "Friday",
        "Суббота": "Saturday",
        "Воскресенье": "Sunday"
    },
    "en": {
        "Monday": "Monday",
        "Tuesday": "Tuesday",
        "Wednesday": "Wednesday",
        "Thursday": "Thursday",
        "Friday": "Friday",
        "Saturday": "Saturday",
        "Sunday": "Sunday"
    }
}

menu_data = {
    "Monday": "Menu for Monday",
    "Tuesday": "Menu for Tuesday",
    "Wednesday": "Menu for Wednesday",
    "Thursday": "Menu for Thursday",
    "Friday": "Menu for Friday",
    "Saturday": "Menu for Saturday",
    "Sunday": "Menu for Sunday"
}


# ================== СОСТОЯНИЯ ==================

class Form(StatesGroup):
    language = State()
    description = State()
    edit_menu = State()


# ================== ВСПОМОГАТЕЛЬНЫЕ ==================

async def get_lang(state: FSMContext):
    data = await state.get_data()
    return data.get("lang", "ru")


async def show_main_menu(message: Message, state: FSMContext):
    lang = await get_lang(state)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=translations[lang]["menu"])],
            [KeyboardButton(text=translations[lang]["sales"])],
            [KeyboardButton(text=translations[lang]["problem"])],
            [KeyboardButton(text=translations[lang]["suggestion"])]
        ],
        resize_keyboard=True
    )

    await message.answer(translations[lang]["main_menu"], reply_markup=keyboard)


# ================== START ==================

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )
    await state.set_state(Form.language)
    await message.answer("Choose language / Выберите язык:", reply_markup=keyboard)


@dp.message(Form.language)
async def set_language(message: Message, state: FSMContext):
    if message.text == "🇷🇺 Русский":
        await state.update_data(lang="ru")
    elif message.text == "🇬🇧 English":
        await state.update_data(lang="en")
    else:
        return

    await state.set_state(None)  # состояние сбрасываем, язык сохраняется
    await show_main_menu(message, state)


# ================== ОСНОВНОЙ ОБРАБОТЧИК ==================

@dp.message()
async def main_handler(message: Message, state: FSMContext):

    if is_spam(message.from_user.id):
        await message.answer((await get_lang(state) == "ru" and translations["ru"]["spam"]) or translations["en"]["spam"])
        return

    lang = await get_lang(state)
    text = message.text

    if text == translations[lang]["cancel"]:
        await state.set_state(None)
        await message.answer(translations[lang]["cancelled"])
        await show_main_menu(message, state)
        return

    if text == translations[lang]["menu"]:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=day)] for day in days[lang]],
            resize_keyboard=True
        )
        await message.answer(translations[lang]["choose_day"], reply_markup=keyboard)
        return

    if text in days[lang]:
        eng_day = days[lang][text]
        await message.answer(menu_data[eng_day])
        await show_main_menu(message, state)
        return

    if text == translations[lang]["sales"]:
        await message.answer(translations[lang]["no_sales"])
        await show_main_menu(message, state)
        return

    if text == translations[lang]["problem"]:
        await state.update_data(category="Problem")
        await state.set_state(Form.description)
        await message.answer(translations[lang]["write_problem"],
                             reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[[KeyboardButton(text=translations[lang]["cancel"])]],
                                 resize_keyboard=True))
        return

    if text == translations[lang]["suggestion"]:
        await state.update_data(category="Suggestion")
        await state.set_state(Form.description)
        await message.answer(translations[lang]["write_suggestion"],
                             reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[[KeyboardButton(text=translations[lang]["cancel"])]],
                                 resize_keyboard=True))
        return


# ================== ПРИЁМ ЗАЯВОК ==================

@dp.message(Form.description)
async def receive_ticket(message: Message, state: FSMContext):
    global ticket_counter

    user_id = message.from_user.id
    lang = await get_lang(state)

    cooldown = ticket_cooldown(user_id)
    if cooldown > 0:
        await message.answer(translations[lang]["cooldown"].format(cooldown))
        return

    text = message.text or message.caption or ""

    if len(text) > 1000:
        await message.answer(translations[lang]["too_long"])
        return

    if contains_links(text):
        await message.answer(translations[lang]["links_blocked"])
        return

    data = await state.get_data()
    category = data.get("category", "Unknown")

    ticket_counter += 1

    photo = message.photo[-1].file_id if message.photo else None

    ticket_text = f"""
📩 Ticket #{ticket_counter}
👤 @{message.from_user.username}
🆔 {user_id}
📂 {category}

{text}
"""

    for manager in MANAGER_IDS:
        if photo:
            await bot.send_photo(manager, photo=photo, caption=ticket_text)
        else:
            await bot.send_message(manager, ticket_text)

    await message.answer(translations[lang]["ticket_sent"])
    await state.set_state(None)
    await show_main_menu(message, state)


# ================== ЗАПУСК ==================

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
