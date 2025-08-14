
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Твой Telegram ID для получения отчетов

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# FSM
class Form(StatesGroup):
    contract = State()
    static_id = State()
    quantity = State()
    photo = State()

# Кнопки контрактов
def get_contract_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Ателье III - 1000", "Товар с корабля - 600")
    kb.add("Апельсины - 24", "Шампиньоны - 80")
    kb.add("Сосна - 100", "Пшеница - 250")
    return kb

# Кнопка вернуться назад
def get_back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Вернуться назад")
    return kb

# Старт
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    await Form.contract.set()
    await message.answer("Выберите контракт:", reply_markup=get_contract_keyboard())

# Выбор контракта
@dp.message_handler(state=Form.contract)
async def process_contract(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Выберите контракт:", reply_markup=get_contract_keyboard())
        return

    contracts = ["Ателье III - 1000", "Товар с корабля - 600",
                 "Апельсины - 24", "Шампиньоны - 80", "Сосна - 100", "Пшеница - 250"]
    if message.text not in contracts:
        await message.answer("Пожалуйста, выберите контракт с кнопок ниже.")
        return

    await state.update_data(contract=message.text)
    await Form.next()  # static_id
    await message.answer("Укажите ваш статический ID:", reply_markup=get_back_keyboard())

# Ввод статического ID
@dp.message_handler(state=Form.static_id)
async def process_static_id(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await Form.contract.set()
        await message.answer("Выберите контракт:", reply_markup=get_contract_keyboard())
        return
    if not message.text.isdigit():
        await message.answer("ID должен быть числом. Введите снова:")
        return
    await state.update_data(static_id=int(message.text))
    await Form.next()  # quantity
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=get_back_keyboard())

# Ввод количества
@dp.message_handler(state=Form.quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await Form.static_id.set()
        await message.answer("Укажите ваш статический ID:", reply_markup=get_back_keyboard())
        return
    if not message.text.isdigit():
        await message.answer("Количество должно быть числом. Введите снова:")
        return
    await state.update_data(quantity=int(message.text))
    await Form.next()  # photo
    await message.answer("Пришлите скриншот для отчёта:", reply_markup=get_back_keyboard())

# Получение фото
@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo = message.photo[-1].file_id
    await bot.send_photo(chat_id=ADMIN_ID, photo=photo,
                         caption=f"Новый отчет:\nКонтракт: {data['contract']}\n"
                                 f"Статический ID: {data['static_id']}\n"
                                 f"Количество: {data['quantity']}")
    await message.answer("Отчет принят👌", reply_markup=get_contract_keyboard())
    # Сброс состояния и возврат к первому шагу
    await Form.contract.set()
    await message.answer("Выберите контракт:", reply_markup=get_contract_keyboard())
    # Проверка "Вернуться назад" на фото
@dp.message_handler(lambda message: message.text == "Вернуться назад", state=Form.photo)
async def back_from_photo(message: types.Message):
    await Form.quantity.set()
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=get_back_keyboard())

# Все остальные сообщения, если не фото и не кнопка
@dp.message_handler(state=Form.photo)
async def check_photo(message: types.Message):
    await message.answer("Пожалуйста, пришлите фото или вернитесь назад.")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
