"""Bank system: /bank, /deposit [amount], /withdraw [amount]"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user
from database.engine import async_session
from database.models import User

router = Router()


@router.message(F.text == "/bank")
async def cmd_bank(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    text = (
        f"🏦 <b>Банк</b>\n\n"
        f"На счету: {user.bank:,} монет\n"
        f"В кошельке: {user.coins:,} монет\n\n"
        f"Команды:\n"
        f"  /deposit [сумма] — положить в банк\n"
        f"  /withdraw [сумма] — снять из банка\n"
        f"  /deposit all — положить все монеты\n"
        f"  /withdraw all — снять все монеты"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/deposit"))
async def cmd_deposit(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:]
    if not args:
        await message.answer("Формат: /deposit [сумма] или /deposit all")
        return

    if args[0].lower() == "all":
        amount = user.coins
    else:
        try:
            amount = int(args[0])
        except ValueError:
            await message.answer("❌ Введите число.")
            return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть положительной.")
        return

    if user.coins < amount:
        await message.answer(f"❌ Недостаточно монет. У вас: {user.coins:,}")
        return

    async with async_session() as s:
        u = await s.get(User, message.from_user.id)
        u.coins -= amount
        u.bank += amount
        await s.commit()

    await message.answer(f"🏦 Положено в банк: {amount:,} монет\nНа счету: {user.bank + amount:,}")


@router.message(F.text.startswith("/withdraw"))
async def cmd_withdraw(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:]
    if not args:
        await message.answer("Формат: /withdraw [сумма] или /withdraw all")
        return

    if args[0].lower() == "all":
        amount = user.bank
    else:
        try:
            amount = int(args[0])
        except ValueError:
            await message.answer("❌ Введите число.")
            return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть положительной.")
        return

    if user.bank < amount:
        await message.answer(f"❌ Недостаточно средств в банке. На счету: {user.bank:,}")
        return

    async with async_session() as s:
        u = await s.get(User, message.from_user.id)
        u.bank -= amount
        u.coins += amount
        await s.commit()

    await message.answer(f"🏦 Снято из банка: {amount:,} монет\nВ кошельке: {user.coins + amount:,}")
