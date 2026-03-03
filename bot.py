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

tickets = {}
ticket_counter = 0

# ================= МЕНЮ =================

menu_data = {
    "Понедельник": "Меню на понедельник",
    "Вторник": "Меню на вторник",
    "Среда": "Меню на среду",
    "Четверг": "Меню на четверг",
    "Пятница": "Меню на пятницу",
    "Суббота": "Меню на субботу",
    "Воскресенье": "Меню на воскресенье"
}

# ================= СОСТОЯНИЯ =================

class Form(StatesGroup):
    description = State()
    edit_day = State()
    edit_text = State()

# ================= ГЛАВНОЕ МЕНЮ =================

async def show_main_menu(message: Message):
    buttons = [
        [KeyboardButton(text="🍽 Меню")],
        [KeyboardButton(text="🚫 Проблема")],
        [KeyboardButton(text="💡 Предложение")]
    ]

    if message.from_user.id in MANAGER_IDS:
        buttons.append([KeyboardButton(text="📩 Заявки")])

    if message.from_user.id == ADMIN_ID:
        buttons.append([KeyboardButton(text="🛠 Админ панель")])

    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Главное меню:", reply_markup=keyboard)

# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):
    await show_main_menu(message)

# ================= ПРОСМОТР МЕНЮ =================

@dp.message(StateFilter(None), F.text == "🍽 Меню")
async def show_days(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=day)] for day in menu_data],
        resize_keyboard=True
    )
    await message.answer("Выберите день:", reply_markup=keyboard)

@dp.message(StateFilter(None), F.text.in_(menu_data.keys()))
async def show_menu(message: Message):
    await message.answer(menu_data[message.text])
    await show_main_menu(message)

# ================= СОЗДАНИЕ ЗАЯВКИ =================

@dp.message(StateFilter(None), F.text.in_(["🚫 Проблема", "💡 Предложение"]))
async def create_ticket(message: Message, state: FSMContext):
    await state.set_state(Form.description)
    await message.answer("Опишите ситуацию. Можно прикрепить фото.\n\n❌ Отмена")

@dp.message(Form.description)
async def receive_ticket(message: Message, state: FSMContext):
    global ticket_counter

    if message.text == "❌ Отмена":
        await state.clear()
        await show_main_menu(message)
        return

    ticket_counter += 1
    user_id = message.from_user.id
    text = message.text or message.caption or ""

    tickets[ticket_counter] = {
        "user_id": user_id,
        "manager_id": None,
        "status": "open"
    }

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"Ответить #{ticket_counter}")],
            [KeyboardButton(text=f"Закрыть #{ticket_counter}")]
        ],
        resize_keyboard=True
    )

    for manager in MANAGER_IDS:
        if message.photo:
            await bot.send_photo(
                manager,
                message.photo[-1].file_id,
                caption=f"📩 Новая заявка #{ticket_counter}\n\n{text}",
                reply_markup=keyboard
            )
        else:
            await bot.send_message(
                manager,
                f"📩 Новая заявка #{ticket_counter}\n\n{text}",
                reply_markup=keyboard
            )

    await message.answer("✅ Заявка отправлена!")
    await state.clear()
    await show_main_menu(message)

# ================= СПИСОК ЗАЯВОК =================

@dp.message(StateFilter(None), F.text == "📩 Заявки")
async def manager_tickets_list(message: Message):
    if message.from_user.id not in MANAGER_IDS:
        return

    open_tickets = [
        tid for tid, data in tickets.items()
        if data["status"] == "open"
    ]

    if not open_tickets:
        await message.answer("Нет открытых заявок.")
        return

    text = "📩 Открытые заявки:\n\n"
    for tid in open_tickets:
        manager = tickets[tid]["manager_id"]
        status = "в работе" if manager else "свободна"
        text += f"#{tid} ({status})\n"

    await message.answer(text)

# ================= ПОДКЛЮЧЕНИЕ =================

@dp.message(StateFilter(None), F.text.startswith("Ответить #"))
async def manager_connect(message: Message):
    if message.from_user.id not in MANAGER_IDS:
        return

    ticket_id = int(message.text.split("#")[1])

    if ticket_id not in tickets:
        return

    if tickets[ticket_id]["manager_id"]:
        await message.answer("❗ Заявка уже в работе.")
        return

    tickets[ticket_id]["manager_id"] = message.from_user.id
    await message.answer(f"🟢 Вы подключились к заявке #{ticket_id}")
    await bot.send_message(
        tickets[ticket_id]["user_id"],
        "👨‍💼 Менеджер подключился к вашей заявке."
    )

# ================= ЗАКРЫТИЕ =================

@dp.message(StateFilter(None), F.text.startswith("Закрыть #"))
async def close_ticket(message: Message):
    if message.from_user.id not in MANAGER_IDS:
        return

    ticket_id = int(message.text.split("#")[1])

    if ticket_id not in tickets:
        return

    tickets[ticket_id]["status"] = "closed"

    await bot.send_message(
        tickets[ticket_id]["user_id"],
        "✅ Ваша заявка закрыта."
    )

    await message.answer(f"🔴 Заявка #{ticket_id} закрыта.")

# ================= АДМИН ПАНЕЛЬ =================

@dp.message(StateFilter(None), F.text == "🛠 Админ панель")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Редактировать меню")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )

    await message.answer("🛠 Панель администратора", reply_markup=keyboard)

# ================= СТАТИСТИКА =================

@dp.message(StateFilter(None), F.text == "📊 Статистика")
async def stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    total = len(tickets)
    open_count = len([t for t in tickets.values() if t["status"] == "open"])
    closed_count = total - open_count

    await message.answer(
        f"📊 Статистика:\n\n"
        f"Всего заявок: {total}\n"
        f"Открытых: {open_count}\n"
        f"Закрытых: {closed_count}"
    )

# ================= РЕДАКТИРОВАНИЕ МЕНЮ =================

@dp.message(StateFilter(None), F.text == "📅 Редактировать меню")
async def edit_menu(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=day)] for day in menu_data] + [[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

    await state.set_state(Form.edit_day)
    await message.answer("Выберите день:", reply_markup=keyboard)

@dp.message(Form.edit_day)
async def choose_day(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await show_main_menu(message)
        return

    if message.text not in menu_data:
        return

    await state.update_data(edit_day=message.text)
    await state.set_state(Form.edit_text)
    await message.answer(f"Введите новый текст для {message.text}\n\n❌ Отмена")

@dp.message(Form.edit_text)
async def save_menu(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await show_main_menu(message)
        return

    data = await state.get_data()
    day = data.get("edit_day")

    menu_data[day] = message.text

    await message.answer(f"✅ Меню на {day} обновлено")
    await state.clear()
    await show_main_menu(message)

# ================= НАЗАД =================

@dp.message(StateFilter(None), F.text == "⬅ Назад")
async def back(message: Message):
    await show_main_menu(message)

# ================= ЖИВОЙ ЧАТ (ПОСЛЕДНИЙ) =================

@dp.message(StateFilter(None))
async def live_chat(message: Message):
    user_id = message.from_user.id

    # Клиент пишет
    for ticket_id, data in tickets.items():
        if data["user_id"] == user_id and data["status"] == "open":
            manager_id = data["manager_id"]
            if manager_id:
                if message.photo:
                    await bot.send_photo(manager_id, message.photo[-1].file_id)
                else:
                    await bot.send_message(
                        manager_id,
                        f"💬 #{ticket_id} Клиент:\n{message.text}"
                    )
            return

    # Менеджер пишет
    if user_id in MANAGER_IDS:
        for ticket_id, data in tickets.items():
            if data["manager_id"] == user_id and data["status"] == "open":
                if message.photo:
                    await bot.send_photo(data["user_id"], message.photo[-1].file_id)
                else:
                    await bot.send_message(
                        data["user_id"],
                        f"💬 Менеджер:\n{message.text}"
                    )
                return

# ================= ЗАПУСК =================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
