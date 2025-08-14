
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 361821337  # <-- Твой Telegram ID

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния пользователя
class ReportStates(StatesGroup):
    choosing_contract = State()
    entering_id = State()
    entering_quantity = State()
    sending_photo = State()

# Кнопки контрактов
contract_buttons = [
    "Ателье III - 1000",
    "Товар с корабля - 600",
    "Апельсины - 24",
    "Шампиньоны - 80",
    "Сосна - 100",
    "Пшеница - 250"
]

def contract_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in contract_buttons:
        kb.add(KeyboardButton(c))
    return kb

def back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Вернуться назад"))
    return kb

# Старт
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "Выберите контракт:",
        reply_markup=contract_keyboard()
    )
    await ReportStates.choosing_contract.set()

# Выбор контракта
@dp.message_handler(state=ReportStates.choosing_contract)
async def contract_chosen(message: types.Message, state: FSMContext):
    if message.text not in contract_buttons:
        await message.answer("Пожалуйста, выберите одну из кнопок ниже.", reply_markup=contract_keyboard())
        return
    await state.update_data(contract=message.text)
    await message.answer("Укажите ваш статический ID:", reply_markup=back_keyboard())
    await ReportStates.entering_id.set()

# Ввод статического ID
@dp.message_handler(state=ReportStates.entering_id)
async def enter_id(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Выберите контракт:", reply_markup=contract_keyboard())
        await ReportStates.choosing_contract.set()
        return
    if not message.text.isdigit():
        await message.answer("Статический ID должен быть числом. Попробуйте ещё раз.")
        return
    await state.update_data(static_id=int(message.text))
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_keyboard())
    await ReportStates.entering_quantity.set()

# Ввод количества
@dp.message_handler(state=ReportStates.entering_quantity)
async def enter_quantity(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Укажите ваш статический ID:", reply_markup=back_keyboard())
        await ReportStates.entering_id.set()
        return
    if not message.text.isdigit():
        await message.answer("Количество должно быть числом. Попробуйте ещё раз.")
        return
    await state.update_data(quantity=int(message.text))
    await message.answer("Пришлите скриншот для отчёта:", reply_markup=back_keyboard())
    await ReportStates.sending_photo.set()

# Отправка фото
@dp.message_handler(content_types=types.ContentType.PHOTO, state=ReportStates.sending_photo)
async def send_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(
        ADMIN_ID,
        f"Новый отчет!\n"
        f"Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"Контракт: {data['contract']}\n"
        f"Статический ID: {data['static_id']}\n"
        f"Количество: {data['quantity']}"
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
    await message.answer("Отчет принят👌", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

# Кнопка "Вернуться назад" на этапе фото
@dp.message_han_
