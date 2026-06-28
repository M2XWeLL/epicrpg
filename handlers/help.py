from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.crud import get_user
from utils.formatters import format_help
from data.items_info import find_item

router = Router()


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    user = await get_user(message.from_user.id)
    area = user.area if user else 1
    lang = user.lang if user else "en"
    text = format_help(area, lang)
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "cmd:/help")
async def cb_help(callback: CallbackQuery):
    await callback.answer()
    user = await get_user(callback.from_user.id)
    area = user.area if user else 1
    lang = user.lang if user else "en"
    text = format_help(area, lang)
    await callback.message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/help "))
async def cmd_help_item(message: Message):
    user = await get_user(message.from_user.id)
    lang = user.lang if user else "en"

    query = message.text[len("/help "):].strip()
    if not query:
        area = user.area if user else 1
        await message.answer(format_help(area, lang), parse_mode="HTML")
        return

    result = find_item(query)
    if not result:
        if lang == "ru":
            text = f"❌ Предмет «{query}» не найден.\n\nПосмотри все команды: /help"
        else:
            text = f"❌ Item «{query}» not found.\n\nSee all commands with \"help\""
        await message.answer(text, parse_mode="HTML")
        return

    key, info = result

    if lang == "ru":
        text = (
            f"<b>{query.replace('_', ' ').title()}</b>\n"
            f"{info['emoji']} {info['desc_ru']}\n"
            f"{info['obtain_ru']}\n\n"
            f"Стоимость продажи\n"
            f"{info['price']:,} coins\n\n"
            f"Не то что искали? Посмотри все команды: /help"
        )
    else:
        text = (
            f"<b>{query.replace('_', ' ').title()}</b>\n"
            f"{info['emoji']} {info['desc_en']}\n"
            f"{info['obtain_en']}\n\n"
            f"Sale Value\n"
            f"{info['price']:,} coins\n\n"
            f"not what you were looking for? see all commands with \"help\""
        )

    await message.answer(text, parse_mode="HTML")
