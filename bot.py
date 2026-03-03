import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
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

promo_text = "🔥 Сегодня специальных акций нет."

# ================= СОСТОЯНИЯ =================

class Form(StatesGroup):
    description = State()
    edit_day = State()
    edit_menu_text = State()
    edit_promo = State()

# ================= КЛАВИАТУРЫ =================

def main_keyboard(user_id):
    buttons = [
        [KeyboardButton(text="🍽 Меню")],
        [KeyboardButton(text="🔥 Акции")],
        [KeyboardButton(text="🚫 Проблема")],
        [KeyboardButton(text="💡 Предложение")]
    ]

    if user_id in MANAGER_IDS:
        buttons.append([KeyboardButton(text="📩 Заявки")])

    if user_id in MANAGER_IDS or user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙ Управление")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )

def manage_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Редактировать меню")],
            [KeyboardButton(text="🔥 Редактировать акции")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )

# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))

# ================= МЕНЮ =================

@dp.message(StateFilter(None), F.text == "🍽 Меню")
async def show_days(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=day)] for day in menu_data] +
                 [[KeyboardButton(text="⬅ Назад")]],
        resize_keyboard=True
    )
    await message.answer("Выберите день:", reply_markup=keyboard)

@dp.message(StateFilter(None), F.text.in_(menu_data.keys()))
async def show_menu(message: Message):
    await message.answer(menu_data[message.text])

# ================= АКЦИИ =================

@dp.message(StateFilter(None), F.text == "🔥 Акции")
async def show_promo(message: Message):
    await message.answer(promo_text)

# ================= УПРАВЛЕНИЕ =================

@dp.message(StateFilter(None), F.text == "⚙ Управление")
async def manage_panel(message: Message):
    if message.from_user.id not in MANAGER_IDS and message.from_user.id != ADMIN_ID:
        return

    await message.answer("Панель управления:", reply_markup=manage_keyboard())

# ================= РЕДАКТИРОВАНИЕ МЕНЮ =================

@dp.message(StateFilter(None), F.text == "📅 Редактировать меню")
async def edit_menu_start(message: Message, state: FSMContext):
    await state.set_state(Form.edit_day)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=day)] for day in menu_data] +
                 [[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

    await message.answer("Выберите день для редактирования:", reply_markup=keyboard)

@dp.message(Form.edit_day)
async def choose_day(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))
        return

    if message.text not in menu_data:
        return

    await state.update_data(selected_day=message.text)
    await state.set_state(Form.edit_menu_text)
    await message.answer("Введите новый текст меню:", reply_markup=cancel_keyboard())

@dp.message(Form.edit_menu_text)
async def save_menu(message: Message, state: FSMContext):
    if message.text in ["❌ Отмена", "⬅ Назад"]:
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))
        return

    data = await state.get_data()
    day = data["selected_day"]

    menu_data[day] = message.text

    await state.clear()
    await message.answer("✅ Меню обновлено.",
                         reply_markup=main_keyboard(message.from_user.id))

# ================= РЕДАКТИРОВАНИЕ АКЦИЙ =================

@dp.message(StateFilter(None), F.text == "🔥 Редактировать акции")
async def edit_promo_start(message: Message, state: FSMContext):
    await state.set_state(Form.edit_promo)
    await message.answer("Введите новый текст акции:", reply_markup=cancel_keyboard())

@dp.message(Form.edit_promo)
async def save_promo(message: Message, state: FSMContext):
    global promo_text

    if message.text in ["❌ Отмена", "⬅ Назад"]:
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))
        return

    promo_text = message.text

    await state.clear()
    await message.answer("✅ Акции обновлены.",
                         reply_markup=main_keyboard(message.from_user.id))

# ================= СОЗДАНИЕ ЗАЯВКИ =================

@dp.message(StateFilter(None), F.text.in_(["🚫 Проблема", "💡 Предложение"]))
async def create_ticket(message: Message, state: FSMContext):
    await state.set_state(Form.description)
    await message.answer("Опишите ситуацию:", reply_markup=cancel_keyboard())

@dp.message(Form.description)
async def receive_ticket(message: Message, state: FSMContext):
    global ticket_counter

    if message.text in ["❌ Отмена", "⬅ Назад"]:
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))
        return

    ticket_counter += 1

    tickets[ticket_counter] = {
        "user_id": message.from_user.id,
        "manager_id": None,
        "status": "open"
    }

    for manager in MANAGER_IDS:
        await bot.send_message(
            manager,
            f"📩 Новая заявка #{ticket_counter}\n\n{message.text}"
        )

    await state.clear()
    await message.answer("✅ Заявка отправлена!",
                         reply_markup=main_keyboard(message.from_user.id))

# ================= LIVE CHAT =================

@dp.message()
async def live_chat(message: Message):
    user_id = message.from_user.id

    for tid, data in tickets.items():
        if data["user_id"] == user_id and data["status"] == "open":
            if data["manager_id"]:
                await bot.send_message(
                    data["manager_id"],
                    f"💬 #{tid} Клиент:\n{message.text}"
                )
            return

    if user_id in active_manager_ticket:
        tid = active_manager_ticket[user_id]
        if tickets[tid]["status"] == "open":
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
