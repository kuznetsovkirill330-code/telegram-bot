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

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("T8740554601:AAGB4AbrvPSYMd5dZTASkfvX2d3h23gV1QA")

ADMIN_ID = 1896626491
MANAGER_IDS = [1896626491]

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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

class Form(StatesGroup):
    description = State()
    edit_day = State()
    edit_text = State()
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

# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))

# ================= СОЗДАНИЕ ЗАЯВКИ =================

@dp.message(StateFilter(None), F.text.in_(["🚫 Проблема", "💡 Предложение"]))
async def create_ticket(message: Message, state: FSMContext):
    await state.set_state(Form.description)
    await message.answer(
        "Опишите ситуацию:",
        reply_markup=cancel_keyboard()
    )

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

    await message.answer(
        "✅ Заявка отправлена!",
        reply_markup=main_keyboard(message.from_user.id)
    )

    await state.clear()

# ================= СПИСОК ЗАЯВОК =================

@dp.message(StateFilter(None), F.text == "📩 Заявки")
async def list_tickets(message: Message):
    if message.from_user.id not in MANAGER_IDS:
        return

    open_tickets = [tid for tid, t in tickets.items() if t["status"] == "open"]

    if not open_tickets:
        await message.answer("Нет открытых заявок.")
        return

    text = "📩 Открытые заявки:\n"
    keyboard_buttons = []

    for tid in open_tickets:
        status = "в работе" if tickets[tid]["manager_id"] else "свободна"
        text += f"#{tid} ({status})\n"
        keyboard_buttons.append([KeyboardButton(text=f"Ответить #{tid}")])
        keyboard_buttons.append([KeyboardButton(text=f"Закрыть #{tid}")])

    keyboard_buttons.append([KeyboardButton(text="⬅ Назад")])

    await message.answer(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
    )

# ================= ПОДКЛЮЧЕНИЕ =================

@dp.message(StateFilter(None), F.text.startswith("Ответить #"))
async def connect_ticket(message: Message):
    if message.from_user.id not in MANAGER_IDS:
        return

    ticket_id = int(message.text.split("#")[1])

    if ticket_id not in tickets or tickets[ticket_id]["status"] != "open":
        await message.answer("Заявка недоступна.")
        return

    tickets[ticket_id]["manager_id"] = message.from_user.id
    active_manager_ticket[message.from_user.id] = ticket_id

    await message.answer(
        f"🟢 Вы подключились к заявке #{ticket_id}",
        reply_markup=ReplyKeyboardRemove()
    )

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

    if message.from_user.id in active_manager_ticket:
        del active_manager_ticket[message.from_user.id]

    await bot.send_message(
        tickets[ticket_id]["user_id"],
        "✅ Ваша заявка закрыта."
    )

    await message.answer(
        f"🔴 Заявка #{ticket_id} закрыта.",
        reply_markup=main_keyboard(message.from_user.id)
    )

# ================= НАЗАД =================

@dp.message(StateFilter(None), F.text == "⬅ Назад")
async def back(message: Message):
    await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))

# ================= LIVE CHAT =================

@dp.message(StateFilter(None))
async def live_chat(message: Message):
    user_id = message.from_user.id

    # клиент
    for tid, data in tickets.items():
        if data["user_id"] == user_id and data["status"] == "open":
            manager_id = data["manager_id"]
            if manager_id:
                await bot.send_message(
                    manager_id,
                    f"💬 #{tid} Клиент:\n{message.text}"
                )
            return

    # менеджер
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
