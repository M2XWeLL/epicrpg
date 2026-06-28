"""Returning Event handler — /returning commands."""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, update_last_active
from game.returning import (
    check_and_start_returning, get_returning_info, claim_superdaily,
    get_returning_shop, buy_returning_shop, get_returning_quest,
    claim_returning_quest,
)

router = Router()


@router.message(F.text.startswith("/returning"))
async def cmd_returning(message: Message):
    args = message.text.split()[1:]

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    # Update last_active and check for returning event
    await update_last_active(message.from_user.id)
    welcome = await check_and_start_returning(message.from_user.id)
    if welcome:
        await message.answer(welcome["message"], parse_mode="HTML")
        return

    if not args:
        result = await get_returning_info(message.from_user.id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    sub = args[0].lower()

    if sub == "info":
        result = await get_returning_info(message.from_user.id)
    elif sub == "superdaily":
        result = await claim_superdaily(message.from_user.id)
    elif sub == "shop":
        result = await get_returning_shop()
    elif sub == "buy" and len(args) >= 2:
        result = await buy_returning_shop(message.from_user.id, args[1])
    elif sub == "quest":
        if len(args) >= 2 and args[1].lower() == "claim":
            result = await claim_returning_quest(message.from_user.id)
        else:
            result = await get_returning_quest(message.from_user.id)
    else:
        result = {
            "success": True,
            "message": (
                "🎉 <b>Событие Возвращение</b>\n\n"
                "Команды:\n"
                "  /returning info — статус события\n"
                "  /returning superdaily — ежедневная награда\n"
                "  /returning quest — квест\n"
                "  /returning shop — магазин\n"
                "  /returning buy [item] — купить из магазина"
            ),
        }

    await message.answer(result["message"], parse_mode="HTML")
