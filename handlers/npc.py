"""
EPIC NPC trading command.
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user
from game.npc import format_trade_rates, npc_buy, npc_sell

router = Router()


@router.message(F.text == "/npc")
@router.message(F.text.startswith("/npc "))
async def cmd_npc(message: Message):
    args = message.text.split()[1:]

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if not args:
        await message.answer(format_trade_rates(user.area), parse_mode="HTML")
        return

    if args[0] == "buy" and len(args) >= 3:
        item = args[1]
        try:
            amount = int(args[2])
        except ValueError:
            await message.answer("Формат: /npc buy [fish/apple/ruby] [кол-во]")
            return
        result = await npc_buy(message.from_user.id, item, amount)
        await message.answer(result["message"])
        if result.get("success"):
            from game.quest import on_npc_trade
            await on_npc_trade(message.from_user.id)
        return

    if args[0] == "sell" and len(args) >= 3:
        item = args[1]
        try:
            amount = int(args[2])
        except ValueError:
            await message.answer("Формат: /npc sell [fish/apple/ruby] [кол-во]")
            return
        result = await npc_sell(message.from_user.id, item, amount)
        await message.answer(result["message"])
        if result.get("success"):
            from game.quest import on_npc_trade
            await on_npc_trade(message.from_user.id)
        return

    await message.answer(
        "🏪 <b>EPIC NPC</b>\n\n"
        "Посмотреть курсы: /npc\n"
        "Купить: /npc buy [fish/apple/ruby] [кол-во]\n"
        "Продать: /npc sell [fish/apple/ruby] [кол-во]",
        parse_mode="HTML"
    )
