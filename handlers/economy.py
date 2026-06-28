"""
Economy commands: daily, weekly, vote, code, donate, give, use, open, lootbox, shop (epic).
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user
from game.economy import (
    get_daily_reward, get_weekly_reward, get_vote_reward, get_vote_info,
    give_coins, use_item, open_lootbox, donate_coins, redeem_code,
    load_shop, buy_item, sell_item,
)
import config

router = Router()


@router.message(F.text == "/daily")
async def cmd_daily(message: Message):
    result = await get_daily_reward(message.from_user.id)
    await message.answer(result["message"])


@router.message(F.text == "/weekly")
async def cmd_weekly(message: Message):
    result = await get_weekly_reward(message.from_user.id)
    await message.answer(result["message"])


@router.message(F.text == "/vote")
@router.message(F.text.startswith("/vote "))
async def cmd_vote(message: Message):
    args = message.text.split()[1:]

    if args and args[0] == "info":
        result = await get_vote_info(message.from_user.id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    if args and args[0] == "tutorial":
        text = (
            "🗳️ <b>Голосование — Туториал</b>\n\n"
            "Голосуйте за бота и получайте награды!\n"
            "Кулдаун: 12 часов.\n\n"
            "📊 <b>Стрик</b> (подряд каждый день):\n"
            "  Стрик 0 → Rare Lootbox\n"
            "  Стрик 1 → Epic Lootbox\n"
            "  Стрики 2-7 → Edgy Lootbox\n\n"
            "🎁 <b>Стрик 7 (максимум):</b>\n"
            "  +25 Арена печенье\n"
            "  +1 Фляга\n"
            "  +1 EPIC монета\n\n"
            "🔄 <b>Всегда при голосовании:</b>\n"
            "  Сброс кулдауна Adventure\n\n"
            "💰 Монеты зависят от вашего уровня.\n\n"
            "Голосовать: /vote\n"
            "Статус: /vote info"
        )
        await message.answer(text, parse_mode="HTML")
        return

    result = await get_vote_reward(message.from_user.id)
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/code"))
async def cmd_code(message: Message):
    args = message.text.split()[1:]
    if not args:
        await message.answer("Формат: /code [промокод]")
        return
    result = await redeem_code(message.from_user.id, args[0])
    await message.answer(result["message"])


@router.message(F.text.startswith("/donate"))
async def cmd_donate(message: Message):
    args = message.text.split()[1:]
    if not args:
        await message.answer(
            "💎 <b>Донат</b>\n\n"
            "Обменяйте монеты на EPIC монеты.\n"
            "Курс: 100 монет = 1 EPIC монета\n\n"
            "Формат: /donate [количество]",
            parse_mode="HTML"
        )
        return
    try:
        amount = int(args[0])
    except ValueError:
        await message.answer("❌ Введите число.")
        return
    result = await donate_coins(message.from_user.id, amount)
    await message.answer(result["message"])


@router.message(F.text.startswith("/give"))
async def cmd_give(message: Message):
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer(
            "💰 <b>Передать монеты</b>\n\n"
            "Формат: /give @username [кол-во]\n"
            "Пример: /give @playerB 5000\n\n"
            "⚠️ Только монеты. Разница TT между игроками не более 2.",
            parse_mode="HTML"
        )
        return

    receiver = args[0].lstrip("@")
    try:
        amount = int(args[1])
    except ValueError:
        await message.answer("❌ Введите число.")
        return

    result = await give_coins(message.from_user.id, receiver, amount)
    await message.answer(result["message"])


@router.message(F.text.startswith("/use"))
async def cmd_use(message: Message):
    args = message.text.split()[1:]
    if not args:
        await message.answer("Формат: /use [предмет]")
        return
    result = await use_item(message.from_user.id, args[0])
    await message.answer(result["message"])


@router.message(F.text.startswith("/open"))
async def cmd_open(message: Message):
    result = await open_lootbox(message.from_user.id)
    await message.answer(result["message"])


@router.message(F.text.startswith("/lootbox"))
async def cmd_lootbox(message: Message):
    args = message.text.split()[1:]
    if not args:
        user = await get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Сначала зарегистрируйтесь: /start")
            return
        text = "📦 <b>Лутбоксы</b>\n\n"
        for box, price in config.LOOTBOX_PRICES.items():
            text += f"  📦 {box} — {price} монет\n"
        text += "\nКупить: /lootbox [тип]"
        await message.answer(text, parse_mode="HTML")
        return

    box_type = args[0]
    price = config.LOOTBOX_PRICES.get(box_type)
    if not price:
        await message.answer("❌ Неизвестный лутбокс.")
        return

    user = await get_user(message.from_user.id)
    if not user or user.coins < price:
        await message.answer("❌ Недостаточно монет.")
        return

    from game.player import remove_coins
    from database.crud import add_materials
    await remove_coins(message.from_user.id, price)
    await add_materials(message.from_user.id, box_type, 1)
    await message.answer(f"📦 Куплен {box_type} за {price} монет!\nОткрыть: /open")


@router.message(F.text == "/shop")
async def cmd_shop(message: Message):
    shop = load_shop()
    text = "🛒 <b>Магазин</b>\n\n"
    for item_id, item in shop.items():
        text += f"{item.get('emoji', '📦')} <b>{item['name']}</b> — {item['buy_price']} coins\n"
    text += "\nКупить: /buy [id] [кол-во]"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/epic shop"))
async def cmd_epic_shop(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    text = (
        f"💎 <b>EPIC Магазин</b>\n"
        f"Ваши EPIC монеты: {user.epic_coins}\n\n"
        f"  💰 1000 монет — 50 EPIC\n"
        f"  ⚔️ Улучшение оружия — 200 EPIC\n"
        f"  🛡️ Улучшение брони — 200 EPIC\n"
        f"  🐾 Случайный питомец — 500 EPIC\n\n"
        f"Купить: /epic buy [id]"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/epic buy"))
async def cmd_epic_buy(message: Message):
    args = message.text.split()[2:] if len(message.text.split()) > 2 else []
    if not args:
        await message.answer("Формат: /epic buy [id]")
        return

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    item_id = args[0]
    epic_prices = {
        "coins_1000": 50,
        "weapon_up": 200,
        "armor_up": 200,
        "random_pet": 500,
    }
    price = epic_prices.get(item_id)
    if not price:
        await message.answer("❌ Неизвестный предмет.")
        return

    if user.epic_coins < price:
        await message.answer("❌ Недостаточно EPIC монет.")
        return

    from database.engine import async_session
    from database.models import User

    async with async_session() as s:
        u = await s.get(User, message.from_user.id)
        u.epic_coins -= price

        if item_id == "coins_1000":
            u.coins += 1000
            msg = "💰 Куплено: 1000 монет!"
        elif item_id == "weapon_up":
            from database.crud import get_equipment, set_equipment
            eq = await get_equipment(message.from_user.id)
            new_tier = min(eq.get("weapon_tier", 1) + 1, 15)
            eq["weapon_tier"] = new_tier
            await set_equipment(message.from_user.id, eq)
            msg = f"⚔️ Оружие улучшено до Тир {new_tier}!"
        elif item_id == "armor_up":
            from database.crud import get_equipment, set_equipment
            eq = await get_equipment(message.from_user.id)
            new_tier = min(eq.get("armor_tier", 1) + 1, 15)
            eq["armor_tier"] = new_tier
            await set_equipment(message.from_user.id, eq)
            msg = f"🛡️ Броня улучшена до Тир {new_tier}!"
        else:
            msg = "❌ Функция в разработке."

        await s.commit()

    await message.answer(f"💎 {msg}")
