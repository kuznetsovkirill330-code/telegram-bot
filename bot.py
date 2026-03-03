import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
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

# ================= СОЗДАНИЕ ЗАЯВКИ =================

@dp.message(StateFilter(None), F.text.in_(["🚫 Проблема", "💡 Предложение"]))
async def create_ticket(message: Message, state: FSMContext):
    await state.set_state(Form.description)
    await message.answer(
        "Опишите ситуацию.\nВы можете отправить текст или фото с подписью.",
        reply_markup=back_kb()
    )

# ================= ПРИЁМ ЗАЯВКИ (ТЕКСТ ИЛИ ФОТО) =================

@dp.message(Form.description)
async def receive_ticket(message: Message, state: FSMContext):
    global ticket_counter

    ticket_counter += 1

    tickets[ticket_counter] = {
        "user_id": message.from_user.id,
        "manager_id": None,
        "status": "open"
    }

    # Уведомляем менеджеров
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

# ================= ЗАЯВКИ =================

@dp.message(StateFilter(None), F.text == "📩 Заявки")
async def show_tickets(message: Message):
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

@dp.message(F.text.startswith("Заявка #"))
async def open_ticket(message: Message):
    tid = int(message.text.split("#")[1])
    if tid not in tickets:
        return
    await message.answer(f"Заявка #{tid}", reply_markup=ticket_actions_kb(tid))

@dp.message(F.text.startswith("▶ Ответить #"))
async def answer_ticket(message: Message):
    tid = int(message.text.split("#")[1])
    tickets[tid]["manager_id"] = message.from_user.id
    active_manager_ticket[message.from_user.id] = tid
    await message.answer(f"Вы подключились к заявке #{tid}")

@dp.message(F.text.startswith("🔴 Закрыть #"))
async def close_ticket(message: Message):
    tid = int(message.text.split("#")[1])
    tickets[tid]["status"] = "closed"

    await bot.send_message(
        tickets[tid]["user_id"],
        f"✅ Заявка #{tid} закрыта."
    )

    active_manager_ticket.pop(message.from_user.id, None)
    await message.answer("Заявка закрыта.", reply_markup=main_kb(message.from_user.id))

# ================= LIVE CHAT (С ФОТО) =================

@dp.message()
async def chat_router(message: Message):
    user_id = message.from_user.id

    # Клиент пишет
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

    # Менеджер пишет
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
