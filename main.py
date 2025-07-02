import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import logging

# Настройка бота
bot = Bot(token="Api_token")
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Константы
FIRMWARES_DIR = os.path.join(os.path.dirname(__file__), "files")
API_DIR = os.path.join(os.path.dirname(__file__), "api")

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📲 Скачать прошивку")],
        [KeyboardButton(text="⚡ Рут-файлы"), KeyboardButton(text="📚 Гайды")],
        [KeyboardButton(text="🛠 Поддержка")]
    ],
    resize_keyboard=True
)

# Загрузка данных из JSON
def load_json_data(filename):
    try:
        with open(os.path.join(API_DIR, filename), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {filename}: {e}")
        return None

def load_firmwares():
    firmwares = {}
    for filename in os.listdir(FIRMWARES_DIR):
        if filename.endswith(".json"):
            brand = filename.split(".")[0].capitalize()
            try:
                with open(os.path.join(FIRMWARES_DIR, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    firmwares[brand] = data[brand][""]["versions"]
            except Exception as e:
                logging.error(f"Error loading {filename}: {e}")
    return firmwares

FIRMWARES = load_firmwares()

# ===================== ОСНОВНЫЕ КОМАНДЫ =====================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🔧 Добро пожаловать в BloodBox - ваш помощник по Android!\n"
        "Выберите раздел:",
        reply_markup=main_menu
    )

# ===================== РАЗДЕЛ ПРОШИВОК =====================
@dp.message(lambda message: message.text == "📲 Скачать прошивку")
async def firmware_menu(message: types.Message):
    brands = list(FIRMWARES.keys())
    keyboard = [
        [InlineKeyboardButton(text=brand, callback_data=f"brand_{brand}")]
        for brand in sorted(brands)
    ]
    await message.answer(
        "Выберите бренд устройства:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(lambda c: c.data.startswith("brand_"))
async def process_brand(callback: types.CallbackQuery):
    brand = callback.data.split("_")[1]
    if brand not in FIRMWARES:
        await callback.answer("Бренд не найден")
        return
    
    models = list(FIRMWARES[brand].keys())
    keyboard = [
        [InlineKeyboardButton(text=model, callback_data=f"model_{brand}_{model}")]
        for model in sorted(models)
    ]
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    await callback.message.edit_text(
        f"📱 {brand} → Выберите модель:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(lambda c: c.data.startswith("model_"))
async def process_model(callback: types.CallbackQuery):
    _, brand, model = callback.data.split("_")
    if brand not in FIRMWARES or model not in FIRMWARES[brand]:
        await callback.answer("Модель не найдена")
        return
    
    firmwares = FIRMWARES[brand][model]["firmwares"]
    
    keyboard = []
    for idx, fw in enumerate(firmwares):
        btn_text = f"{fw['name']}"
        if "size" in fw:
            btn_text += f" ({fw['size']} MB)"
        keyboard.append(
            [InlineKeyboardButton(text=btn_text, callback_data=f"fw_{brand}_{model}_{idx}")]
        )
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад к брендам", callback_data=f"brand_{brand}"),
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main")
    ])
    
    await callback.message.edit_text(
        f"📱 {brand} → {model}\n\n"
        "Доступные прошивки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(lambda c: c.data.startswith("fw_"))
async def show_firmware(callback: types.CallbackQuery):
    _, brand, model, fw_idx = callback.data.split("_")
    fw_idx = int(fw_idx)
    
    if brand not in FIRMWARES or model not in FIRMWARES[brand]:
        await callback.answer("Прошивка не найдена")
        return
    
    firmwares = FIRMWARES[brand][model]["firmwares"]
    if fw_idx >= len(firmwares):
        await callback.answer("Прошивка не найдена")
        return
    
    firmware = firmwares[fw_idx]
    
    text = f"📱 <b>{brand} {model}</b>\n\n"
    text += f"🔧 <b>{firmware['name']}</b>\n\n"
    
    if "size" in firmware:
        text += f"📦 <b>Размер:</b> {firmware['size']} MB\n"
    if "description" in firmware:
        text += f"\nℹ️ <b>Описание:</b>\n{firmware['description']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Скачать прошивку", url=firmware["url"])],
        [
            InlineKeyboardButton(text="🔙 Назад к прошивкам", callback_data=f"model_{brand}_{model}"),
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main")
        ]
    ])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

# ===================== РАЗДЕЛ РУТ-ФАЙЛОВ =====================
@dp.message(lambda message: message.text == "⚡ Рут-файлы")
async def root_files_menu(message: types.Message):
    root_files = load_json_data("root_files.json")
    if not root_files:
        await message.answer("⚡ Рут-файлы временно недоступны")
        return
    
    keyboard = [
        [InlineKeyboardButton(text=rf["name"], callback_data=f"root_{idx}")]
        for idx, rf in enumerate(root_files)
    ]
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    await message.answer(
        "⚡ Доступные рут-файлы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(lambda c: c.data.startswith("root_"))
async def show_root_file(callback: types.CallbackQuery):
    root_files = load_json_data("root_files.json")
    if not root_files:
        await callback.answer("Рут-файлы временно недоступны")
        return
    
    rf = root_files[int(callback.data.split("_")[1])]
    
    text = f"⚡ <b>{rf['name']}</b>\n\n"
    if "version" in rf:
        text += f"🔹 <b>Версия:</b> {rf['version']}\n"
    if "size" in rf:
        text += f"📦 <b>Размер:</b> {rf['size']} MB\n"
    if "description" in rf:
        text += f"\nℹ️ <b>Описание:</b>\n{rf['description']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Скачать", url=rf["url"])],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_root")]
    ])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

# ===================== РАЗДЕЛ ГАЙДОВ =====================
@dp.message(lambda message: message.text == "📚 Гайды")
async def guides_menu(message: types.Message):
    guides = load_json_data("guides.json")
    if not guides:
        await message.answer("📚 Гайды временно недоступны")
        return
    
    keyboard = [
        [InlineKeyboardButton(text=guide["title"], callback_data=f"guide_{idx}")]
        for idx, guide in enumerate(guides)
    ]
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    await message.answer(
        "📚 Доступные гайды:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(lambda c: c.data.startswith("guide_"))
async def show_guide(callback: types.CallbackQuery):
    guides = load_json_data("guides.json")
    if not guides:
        await callback.answer("Гайды временно недоступны")
        return
    
    guide = guides[int(callback.data.split("_")[1])]
    
    text = f"📖 <b>{guide['title']}</b>\n\n"
    if "description" in guide:
        text += f"🔹 {guide['description']}\n\n"
    text += guide["content"]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_guides")]
    ])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ===================== РАЗДЕЛ ПОДДЕРЖКИ =====================
@dp.message(lambda message: message.text == "🛠 Поддержка")
async def support(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await message.answer(
        "🛠 <b>Техническая поддержка</b>\n\n"
        "По всем вопросам обращайтесь к @stopscam_vbn\n\n"
        "При обращении укажите:\n"
        "1. Модель устройства\n"
        "2. Версию прошивки (если проблема в ней)\n"
        "3. Подробное описание проблемы",
        reply_markup=markup,
        parse_mode="HTML"
    )

# ===================== ОБРАБОТКА КНОПОК "НАЗАД" =====================
@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu
    )
    await callback.message.delete()
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_root")
async def back_to_root_menu(callback: types.CallbackQuery):
    await root_files_menu(callback.message)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_guides")
async def back_to_guides_menu(callback: types.CallbackQuery):
    await guides_menu(callback.message)
    await callback.answer()

# ===================== ЗАПУСК БОТА =====================
if __name__ == "__main__":
    logging.info("Бот запущен!")
    dp.run_polling(bot)
