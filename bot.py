
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Ваш Telegram ID для получения отчетов

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния FSM
class ReportStates(StatesGroup):
    CHOOSING_CONTRACT = State()
    ENTER_ID = State()
    ENTER_QUANTITY = State()
    SEND_PHOTO = State()

# Контракты: (название, callback)
contracts = [
    ("Ателье III - 1000", "contract_1"),
    ("Товар с корабля - 600", "contract_2"),
    ("Апельсины - 24", "contract_3"),
    ("Шампиньоны - 80", "contract_4"),
    ("Сосна - 100", "contract_5"),
    ("Пшеница - 250", "contract_6"),
]

# Кнопка "Вернуться назад"
back_button = ReplyKeyboardMarkup(resize_keyboard=True)
back_button.add(KeyboardButton("Вернуться назад"))

# Приветствие и выбор контракта
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()  # сброс всех предыдущих состояний
    await message.answer("Привет! 👋 Я бот AFK Family для формирования отчетов по контрактам.\nСледуй инструкциям ниже.")
    await show_contract_buttons(message)
    await ReportStates.CHOOSING_CONTRACT.set()

# Функция показа кнопок контрактов
async def show_contract_buttons(message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for name, callback in contracts:
        keyboard.add(InlineKeyboardButton(text=name, callback_data=callback))
    await message.answer("Пожалуйста, выберите контракт:", reply_markup=keyboard)

# Выбор контракта
@dp.callback_query_handler(lambda c: c.data.startswith("contract_"), state=ReportStates.CHOOSING_CONTRACT)
async def choose_contract(call: types.CallbackQuery, state: FSMContext):
    contract_name = next(name for name, callback in contracts if callback == call.data)
    await state.update_data(contract=contract_name)
    await call.message.edit_reply_markup(reply_markup=None)  # убираем кнопки
    await call.message.answer("Укажите ваш статический ID:", reply_markup=back_button)
    await ReportStates.ENTER_ID.set()

# Обработка кнопки "Вернуться назад"
@dp.message_handler(lambda m: m.text == "Вернуться назад", state="*")
async def go_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ReportStates.ENTER_ID.state or current_state == ReportStates.ENTER_QUANTITY.state or current_state == ReportStates.SEND_PHOTO.state:
        await state.finish()
        await show_contract_buttons(message)
        await ReportStates.CHOOSING_CONTRACT.set()

# Ввод статического ID
@dp.message_handler(lambda m: not m.text.isdigit(), state=ReportStates.ENTER_ID)
async def process_invalid_id(message: types.Message):
    await message.reply("Пожалуйста, введите числовой ID!")

@dp.message_handler(lambda m: m.text.isdigit(), state=ReportStates.ENTER_ID)
async def process_id(message: types.Message, state: FSMContext):
    await state.update_data(user_id=int(message.text))
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_button)
    await ReportStates.ENTER_QUANTITY.set()

# Ввод количества
@dp.message_handler(lambda m: not m.text.isdigit(), state=ReportStates.ENTER_QUANTITY)
async def process_invalid_quantity(message: types.Message):
    await message.reply("Пожалуйста, введите числовое значение количества!")

@dp.message_handler(lambda m: m.text.isdigit(), state=ReportStates.ENTER_QUANTITY)
async def process_quantity(message: types.Message, state: FSMContext):
    await state.update_data(quantity=int(message.text))
    await message.answer("Пришлите скриншот для отчёта:", reply_markup=back_button)
    await ReportStates.SEND_PHOTO.set()

# Получение фото
@dp.message_handler(content_types=['photo'], state=ReportStates.SEND_PHOTO)
async def receive_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.reply("Пожалуйста, пришлите именно фото!")
        return
    data = await state.get_data()
    await state.update_data(photo=message.photo[-1].file_id)

    # Отправка админу
    contract = data['contract']
    user_id = data['user_id']
    quantity = data['quantity']
    photo_id = data['photo']
    await bot.send_message(ADMIN_ID, f"Новый отчет:\nКонтракт: {contract}\nСтатический ID: {user_id}\nКоличество: {quantity}")
    await bot.send_photo(ADMIN_ID, photo=photo_id)

    await message.answer("Отчет принят👌")
    # Сброс и возврат к выбору контракта
    await state.finish()
    await show_contract_buttons(message)
    await ReportStates.CHOOSING_CONTRACT.set()

# Игнорирование других сообщений на этапах
@dp.message_handler(state='*')
async def catch_all(message: types.Message):
    await message.reply("Пожалуйста, следуйте инструкциям и используйте кнопки или вводите данные в требуемом формате!")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
