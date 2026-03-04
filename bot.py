import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ================= НАСТРОЙКИ =================

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("8740554601:AAGB4AbrvPSYMd5dZTASkfvX2d3h23gV1QA")

ADMIN_ID = 1896626491
MANAGER_IDS = [1896626491]

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= ДАННЫЕ =================

tickets = {}
active_manager_ticket = {}
ticket_counter = 0

menu_data = {
    "Понедельник": "Меню на понедельник",
    "Вторник": "Меню на вторник",
    "Среда": "Меню на среду",
    "Четверг": "Меню на четверг",
    "Пятница": "Меню на пятницу",
    "Суббота": "Меню на субботу",
    "Воскресенье": "Меню на воскресенье"
}

promo_text = "🔥 Сегодня акций нет."

# ================= СОСТОЯНИЯ =================

class Form(StatesGroup):
    description = State()
    edit_day = State()
    edit_menu_text = State()
    edit_promo = State()

# ================= КЛАВИАТУРЫ =================

def main_kb(user_id):
    buttons = [
        [KeyboardButton(text="🍽 Меню")],
        [KeyboardButton(text="🔥 Акции")],
        [KeyboardButton(text="🚫 Проблема")],
        [KeyboardButton(text="💡 Предложение")]
    ]

    if user_id in MANAGER_IDS or user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="📩 Заявки")])
        buttons.append([KeyboardButton(text="⚙ Управление")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅ Назад")]],
        resize_keyboard=True
    )

def manage_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Редактировать меню")],
            [KeyboardButton(text="🔥 Редактировать акции")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )

def ticket_actions_kb(tid):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"▶ Ответить #{tid}")],
            [KeyboardButton(text=f"🔴 Закрыть #{tid}")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )

# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Главное меню:", reply_markup=main_kb(message.from_user.id))

# ================= НАЗАД =================

@dp.message(F.text == "⬅ Назад")
async def back(message: Message, state: FSMContext):
    await state.clear()
    active_manager_ticket.pop(message.from_user.id, None)
    await message.answer("Главное меню:", reply_markup=main_kb(message.from_user.id))

# ================= МЕНЮ =================

@dp.message(StateFilter(None), F.text == "🍽 Меню")
async def show_days(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=day)] for day in menu_data] +
                 [[KeyboardButton(text="⬅ Назад")]],
        resize_keyboard=True
    )
    await message.answer("Выберите день:", reply_markup=kb)

@dp.message(StateFilter(None), F.text.in_(menu_data.keys()))
async def show_menu(message: Message):
    await message.answer(menu_data[message.text])

# ================= АКЦИИ =================

@dp.message(StateFilter(None), F.text == "🔥 Акции")
async def show_promo(message: Message):
    await message.answer(promo_text, reply_markup=back_kb())

# ================= УПРАВЛЕНИЕ =================

@dp.message(StateFilter(None), F.text == "⚙ Управление")
async def manage_panel(message: Message):
    if message.from_user.id not in MANAGER_IDS and message.from_user.id != ADMIN_ID:
        return
    await message.answer("Панель управления:", reply_markup=manage_kb())

# ================= РЕДАКТИРОВАНИЕ МЕНЮ =================

@dp.message(StateFilter(None), F.text == "📅 Редактировать меню")
async def edit_menu_start(message: Message, state: FSMContext):
    await state.set_state(Form.edit_day)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=day)] for day in menu_data] +
                 [[KeyboardButton(text="⬅ Назад")]],
        resize_keyboard=True
    )

    await message.answer("Выберите день для редактирования:", reply_markup=kb)

@dp.message(Form.edit_day)
async def choose_day(message: Message, state: FSMContext):
    if message.text == "⬅ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb(message.from_user.id))
        return

    if message.text not in menu_data:
        return

    await state.update_data(day=message.text)
    await state.set_state(Form.edit_menu_text)
    await message.answer("Введите новый текст меню:", reply_markup=back_kb())

@dp.message(Form.edit_menu_text)
async def save_menu(message: Message, state: FSMContext):
    if message.text == "⬅ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb(message.from_user.id))
        return

    data = await state.get_data()
    menu_data[data["day"]] = message.text

    await state.clear()
    await message.answer("✅ Меню обновлено.", reply_markup=main_kb(message.from_user.id))

# ================= РЕДАКТИРОВАНИЕ АКЦИЙ =================

@dp.message(StateFilter(None), F.text == "🔥 Редактировать акции")
async def edit_promo_start(message: Message, state: FSMContext):
    await state.set_state(Form.edit_promo)
    await message.answer("Введите новый текст акции:", reply_markup=back_kb())

@dp.message(Form.edit_promo)
async def save_promo(message: Message, state: FSMContext):
    global promo_text

    if message.text == "⬅ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb(message.from_user.id))
        return

    promo_text = message.text

    await state.clear()
    await message.answer("✅ Акции обновлены.", reply_markup=main_kb(message.from_user.id))

# ================= ЗАЯВКИ =================

# ---------- ПРОБЛЕМА ----------

@dp.message(StateFilter(None), F.text == "🚫 Проблема")
async def problem_start(message: Message, state: FSMContext):
    await state.set_state(Form.description)
    await state.update_data(type="problem")

    await message.answer(
        "Нам жаль, что возникла проблема 🙁\n\n"
        "Опишите, пожалуйста, ситуацию как можно подробнее "
        "и при необходимости прикрепите фото.\n\n"
        "Мы обязательно разберёмся и поможем вам как можно быстрее 💛",
        reply_markup=back_kb()
    )


# ---------- ПРЕДЛОЖЕНИЕ ----------

@dp.message(StateFilter(None), F.text == "💡 Предложение")
async def suggestion_start(message: Message, state: FSMContext):
    await state.set_state(Form.description)
    await state.update_data(type="suggestion")

    await message.answer(
        "Поделитесь своими идеями или пожеланиями 😊\n\n"
        "Мы внимательно читаем каждое сообщение и "
        "искренне ценим вашу обратную связь 💛",
        reply_markup=back_kb()
    )

@dp.message(Form.description)
async def receive_ticket(message: Message, state: FSMContext):
    global ticket_counter

    if message.text == "⬅ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb(message.from_user.id))
        return

    ticket_counter += 1

    data = await state.get_data()
ticket_type = data.get("type", "problem")

tickets[ticket_counter] = {
    "user_id": message.from_user.id,
    "manager_id": None,
    "status": "open",
    "type": ticket_type,
    "text": message.text or message.caption,
    "photo": message.photo[-1].file_id if message.photo else None
}

    for manager in MANAGER_IDS:
        if message.photo:
            await bot.send_photo(
                manager,
                photo=message.photo[-1].file_id,
                caption=f"📩 Новая заявка #{ticket_counter}\n\n{message.caption or ''}"
            )
        else:
            await bot.send_message(
                manager,
                f"📩 Новая заявка #{ticket_counter}\n\n{message.text}"
            )

    await state.clear()
    await message.answer("✅ Заявка отправлена!", reply_markup=main_kb(message.from_user.id))
    
# ================= ЗАЯВКИ ДЛЯ МЕНЕДЖЕРА =================

# ---------- РАЗДЕЛ ЗАЯВОК ----------

def tickets_category_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚫 Проблемы")],
            [KeyboardButton(text="💡 Предложения")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )


@dp.message(StateFilter(None), F.text == "📩 Заявки")
async def show_ticket_categories(message: Message):
    if message.from_user.id not in MANAGER_IDS and message.from_user.id != ADMIN_ID:
        return

    await message.answer("Выберите раздел:", reply_markup=tickets_category_kb())


# ---------- СПИСОК ПРОБЛЕМ ----------

@dp.message(StateFilter(None), F.text == "🚫 Проблемы")
async def show_problems(message: Message):
    open_tickets = [
        tid for tid, t in tickets.items()
        if t["status"] == "open" and t["type"] == "problem"
    ]

    if not open_tickets:
        await message.answer("Нет открытых проблем.", reply_markup=tickets_category_kb())
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"Заявка #{tid}")] for tid in open_tickets] +
                 [[KeyboardButton(text="⬅ Назад")]],
        resize_keyboard=True
    )

    await message.answer("Открытые проблемы:", reply_markup=kb)


# ---------- СПИСОК ПРЕДЛОЖЕНИЙ ----------

@dp.message(StateFilter(None), F.text == "💡 Предложения")
async def show_suggestions(message: Message):
    open_tickets = [
        tid for tid, t in tickets.items()
        if t["status"] == "open" and t["type"] == "suggestion"
    ]

    if not open_tickets:
        await message.answer("Нет открытых предложений.", reply_markup=tickets_category_kb())
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"Заявка #{tid}")] for tid in open_tickets] +
                 [[KeyboardButton(text="⬅ Назад")]],
        resize_keyboard=True
    )

    await message.answer("Открытые предложения:", reply_markup=kb)
async def show_tickets(message: Message):
    if message.from_user.id not in MANAGER_IDS and message.from_user.id != ADMIN_ID:
        return

    open_tickets = [tid for tid, t in tickets.items() if t["status"] == "open"]

    if not open_tickets:
        await message.answer("Нет открытых заявок.", reply_markup=main_kb(message.from_user.id))
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"Заявка #{tid}")] for tid in open_tickets] +
                 [[KeyboardButton(text="⬅ Назад")]],
        resize_keyboard=True
    )

    await message.answer("Открытые заявки:", reply_markup=kb)


@dp.message(StateFilter(None), F.text.startswith("Заявка #"))
async def open_ticket(message: Message):
    if message.from_user.id not in MANAGER_IDS and message.from_user.id != ADMIN_ID:
        return

    try:
        tid = int(message.text.split("#")[1])
    except:
        return

    if tid not in tickets or tickets[tid]["status"] != "open":
        await message.answer("Заявка не найдена.")
        return

    ticket = tickets[tid]
    user_id = ticket["user_id"]

    # Получаем информацию о пользователе
    try:
        chat = await bot.get_chat(user_id)
        full_name = chat.full_name
        username = f"@{chat.username}" if chat.username else "Нет username"
    except:
        full_name = "Неизвестно"
        username = "Нет username"

    # Формируем блок информации
    user_info = (
        f"📩 Заявка #{tid}\n\n"
        f"👤 Имя: {full_name}\n"
        f"🆔 ID: {user_id}\n"
        f"🔗 Username: {username}\n\n"
        f"📝 Текст обращения:\n{ticket['text'] or ''}"
    )

    # Если есть фото — отправляем фото с подписью
    if ticket["photo"]:
        await bot.send_photo(
            message.from_user.id,
            photo=ticket["photo"],
            caption=user_info
        )
    else:
        await message.answer(user_info)

    await message.answer(
        "Выберите действие:",
        reply_markup=ticket_actions_kb(tid)
    )


@dp.message(StateFilter(None), F.text.startswith("▶ Ответить #"))
async def answer_ticket(message: Message):
    try:
        tid = int(message.text.split("#")[1])
    except:
        return

    if tid not in tickets or tickets[tid]["status"] != "open":
        return

    tickets[tid]["manager_id"] = message.from_user.id
    active_manager_ticket[message.from_user.id] = tid

    await message.answer(f"Вы подключились к заявке #{tid}")


@dp.message(StateFilter(None), F.text.startswith("🔴 Закрыть #"))
async def close_ticket(message: Message):
    try:
        tid = int(message.text.split("#")[1])
    except:
        return

    if tid not in tickets:
        return

    tickets[tid]["status"] = "closed"

    await bot.send_message(
        tickets[tid]["user_id"],
        f"✅ Заявка #{tid} закрыта."
    )

    active_manager_ticket.pop(message.from_user.id, None)

    await message.answer("Заявка закрыта.", reply_markup=main_kb(message.from_user.id))
    
# ================= LIVE CHAT =================

@dp.message()
async def chat_router(message: Message):
    user_id = message.from_user.id

    for tid, data in tickets.items():
        if data["user_id"] == user_id and data["status"] == "open":
            if data["manager_id"]:
                if message.photo:
                    await bot.send_photo(
                        data["manager_id"],
                        photo=message.photo[-1].file_id,
                        caption=f"💬 #{tid} Клиент:\n{message.caption or ''}"
                    )
                else:
                    await bot.send_message(
                        data["manager_id"],
                        f"💬 #{tid} Клиент:\n{message.text}"
                    )
            return

    if user_id in active_manager_ticket:
        tid = active_manager_ticket[user_id]
        if tickets[tid]["status"] == "open":
            if message.photo:
                await bot.send_photo(
                    tickets[tid]["user_id"],
                    photo=message.photo[-1].file_id,
                    caption=f"💬 Менеджер:\n{message.caption or ''}"
                )
            else:
                await bot.send_message(
                    tickets[tid]["user_id"],
                    f"💬 Менеджер:\n{message.text}"
                )

# ================= ЗАПУСК =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
