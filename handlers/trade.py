"""
Trade command — /trade, /trade [ID], /trade [ID] [amount]
Wiki-accurate resource exchange system.
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user
from game.trade import format_trade_options, execute_trade

router = Router()


@router.message(F.text == "/trade")
@router.message(F.text.startswith("/trade "))
async def cmd_trade(message: Message):
    user_id = message.from_user.id
    args = message.text.split()[1:]

    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if not args:
        await message.answer(format_trade_options(user.max_area), parse_mode="HTML")
        return

    trade_id = args[0].upper()

    # Parse amount
    if len(args) >= 2:
        amount_str = args[1].lower()
        if amount_str == "all":
            # We'll handle "all" in execute_trade by checking inventory
            # For now, pass a large number and let the logic cap it
            from game.trade import get_trade_options
            options = get_trade_options(user.max_area)
            trade = None
            for opt in options:
                if opt["id"].upper() == trade_id:
                    trade = opt
                    break
            if trade:
                from database.crud import get_inventory
                inv = await get_inventory(user_id)
                have = inv.get(trade["give"][0], 0)
                amount = have // trade["give"][1] if trade["give"][1] > 0 else 0
                if amount <= 0:
                    await message.answer("❌ Недостаточно ресурсов для обмена.")
                    return
            else:
                await message.answer(f"❌ Нет сделки с ID '{trade_id}'.")
                return
        else:
            try:
                amount = int(amount_str)
            except ValueError:
                await message.answer("Формат: /trade [ID] (кол-во)")
                return
    else:
        amount = 1

    result = await execute_trade(user_id, trade_id, amount)
    await message.answer(result["message"])
