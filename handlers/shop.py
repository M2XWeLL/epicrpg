import json
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, add_materials, remove_materials
from game.player import remove_coins, add_coins
from game.economy import load_shop, buy_item, sell_item
from config import DATA_DIR

router = Router()


@router.message(F.text.startswith("/buy"))
async def cmd_buy(message: Message):
    args = message.text.split()[1:] if message.text else []
    if not args:
        shop = load_shop()
        text = "🛒 <b>Магазин</b>\n\n"
        for item_id, item in shop.items():
            text += f"{item.get('emoji', '📦')} <b>{item['name']}</b> — {item['buy_price']} coins\n"
        text += "\nКупить: /buy [id] [кол-во]"
        await message.answer(text, parse_mode="HTML")
        return

    item_id = args[0]
    amount = int(args[1]) if len(args) > 1 else 1
    result = await buy_item(message.from_user.id, item_id, amount)
    await message.answer(result["message"])


@router.message(F.text.startswith("/sell"))
async def cmd_sell(message: Message):
    args = message.text.split()[1:] if message.text else []
    if not args:
        await message.answer(
            "💰 <b>Продать ресурсы</b>\n\n"
            "Доступно: wooden_log, epic_log, super_log, apple, banana, potato...\n\n"
            "Продать: /sell [ресурс] [кол-во]",
            parse_mode="HTML"
        )
        return

    material = args[0]
    amount = int(args[1]) if len(args) > 1 else 1
    result = await sell_item(message.from_user.id, material, amount)
    await message.answer(result["message"])
