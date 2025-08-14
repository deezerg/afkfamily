
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")
ADMINS = [int(uid) for uid in os.getenv("ADMINS", "").split(",") if uid]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Кнопки выбора контракта
buttons = [
    "Ателье III - 1000",
    "Товар с корабля - 600",
    "Апельсины - 24",
    "Шампиньоны - 80",
    "Сосна - 100",
    "Пшеница - 250"
]
kb = ReplyKeyboardMarkup(resize_keyboard=True)
for btn in buttons:
    kb.add(KeyboardButton(btn))

user_data = {}

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Выберите контракт:", reply_markup=kb)

@dp.message_handler(commands=["myid"])
async def myid_cmd(message: types.Message):
    await message.answer(f"Ваш user_id: {message.from_user.id}")

@dp.message_handler(lambda msg: msg.text in buttons)
async def contract_chosen(message: types.Message):
    user_data[message.from_user.id] = {"contract": message.text}
    await message.answer("Укажите ваш статический ID:")

@dp.message_handler(lambda msg: message.from_user.id in user_data and "static_id" not in user_data[message.from_user.id])
async def static_id_input(message: types.Message):
    user_data[message.from_user.id]["static_id"] = message.text
    await message.answer("Введите количество позиций к отгрузке:")

@dp.message_handler(lambda msg: message.from_user.id in user_data and "quantity" not in user_data[message.from_user.id])
async def quantity_input(message: types.Message):
    user_data[message.from_user.id]["quantity"] = message.text
    await message.answer("Пришлите скриншот для отчёта.")

@dp.message_handler(content_types=["photo"])
async def handle_photo(message: types.Message):
    if message.from_user.id in user_data:
        data = user_data.pop(message.from_user.id)
        caption = (
            f"Контракт: {data['contract']}
"
            f"Статический ID: {data['static_id']}
"
            f"Количество: {data['quantity']}"
        )
        for admin_id in ADMINS:
            await bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption)
        await message.answer("Отчёт отправлен администратору!")
    else:
        await message.answer("Сначала начните с выбора контракта.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
