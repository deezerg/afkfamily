
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")  # Убедитесь, что переменная окружения BOT_TOKEN задана

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # Telegram ID администратора, куда будут отправляться отчеты

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Состояния бота ---
class Form(StatesGroup):
    contract = State()
    static_id = State()
    quantity = State()
    screenshot = State()

# --- Кнопки для контрактов ---
contracts_buttons = [
    "Ателье III - 1000",
    "Товар с корабля - 600",
    "Апельсины - 24",
    "Шампиньоны - 80",
    "Сосна - 100",
    "Пшеница - 250"
]

def contracts_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in contracts_buttons:
        kb.add(KeyboardButton(c))
    return kb

def back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Вернуться назад"))
    return kb

# --- /start ---
@dp.message_handler(commands=["start"], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()  # Сбрасываем все состояния
    await message.answer("Выберите контракт:", reply_markup=contracts_keyboard())
    await Form.contract.set()

# --- Выбор контракта ---
@dp.message_handler(state=Form.contract)
async def choose_contract(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Выберите контракт:", reply_markup=contracts_keyboard())
        return

    if message.text not in contracts_buttons:
        await message.answer("Пожалуйста, выберите контракт из списка.")
        return

    await state.update_data(contract=message.text)
    await message.answer("Укажите ваш статический ID:", reply_markup=back_keyboard())
    await Form.static_id.set()

# --- Ввод статического ID ---
@dp.message_handler(state=Form.static_id)
async def input_static_id(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Выберите контракт:", reply_markup=contracts_keyboard())
        await Form.contract.set()
        return

    if not message.text.isdigit():
        await message.answer("Статический ID должен быть числом. Попробуйте ещё раз.")
        return

    await state.update_data(static_id=int(message.text))
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_keyboard())
    await Form.quantity.set()

# --- Ввод количества ---
@dp.message_handler(state=Form.quantity)
async def input_quantity(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Укажите ваш статический ID:", reply_markup=back_keyboard())
        await Form.static_id.set()
        return

    if not message.text.isdigit():
        await message.answer("Количество должно быть числом. Попробуйте ещё раз.")
        return

    await state.update_data(quantity=int(message.text))
    await message.answer("Пришлите скриншот для отчёта:", reply_markup=back_keyboard())
    await Form.screenshot.set()

# --- Приём фото ---
@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.screenshot)
async def receive_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    contract = data.get("contract")
    static_id = data.get("static_id")
    quantity = data.get("quantity")
    
    # Отправка админу
    photo = message.photo[-1].file_id  # Берём фото с наибольшим разрешением
    caption = f"Новый отчет:\nКонтракт: {contract}\nСтатический ID: {static_id}\nКоличество: {quantity}"
    await bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=caption)

    await message.answer("Отчет принят👌", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

# --- Проверка "Вернуться назад" при неправильном типе данных ---
@dp.message_handler(state=Form.screenshot)
async def check_photo_type(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_keyboard())
        await Form.quantity.set()
        return
    await message.answer("Пожалуйста, пришлите фото для отчёта.")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
