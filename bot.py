
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import os
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    static_id = State()
    quantity = State()
    screenshot = State()

# Кнопки с контрактами
contracts_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
contracts_keyboard.add(KeyboardButton("Контракт 1"), KeyboardButton("Контракт 2"))

@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    await message.answer("Выберите контракт:", reply_markup=contracts_keyboard)

@dp.message_handler(lambda message: message.text in ["Контракт 1", "Контракт 2"])
async def choose_contract(message: types.Message, state: FSMContext):
    await state.update_data(contract=message.text)
    await Form.static_id.set()
    await message.answer("Укажите ваш статический ID:")

@dp.message_handler(state=Form.static_id)
async def process_static_id(message: types.Message, state: FSMContext):
    await state.update_data(static_id=message.text)
    await Form.next()
    await message.answer("Укажите количество позиций:")

@dp.message_handler(state=Form.quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await Form.next()
    await message.answer("Прикрепите скриншот отчета:")

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.screenshot)
async def process_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Здесь можно сохранить скриншот или обработать его
    await message.answer("Отчет принят!")
    await state.finish()

if name == "__main__":
    executor.start_polling(dp, skip_updates=True)
