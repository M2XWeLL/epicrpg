"""
Horse commands: /horse, /horse info, /horse buy, /horse training,
/horse breeding, /horse race, /horse feed.
"""
from aiogram import Router, F
from aiogram.types import Message
import random
from database.crud import get_user
from game.horses import (
    format_horse_info, horse_training, horse_feed,
    horse_breeding, horse_race, horse_epicness, get_horse_types,
)

router = Router()


@router.message(F.text == "/horse")
@router.message(F.text.startswith("/horse "))
async def cmd_horse(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    from database.engine import async_session
    from database.models import Horse

    async with async_session() as s:
        horse = await s.get(Horse, message.from_user.id)

    if not horse and not args:
        # Show buy menu
        types = get_horse_types()
        text = "🐴 <b>Магазин лошадей</b>\n\n"
        text += "Купить 기본 лошадь: /horse buy\n"
        text += "(Тип определяется случайно, кроме Special/Super Special)"
        await message.answer(text, parse_mode="HTML")
        return

    if not args or args[0] == "info":
        if not horse:
            await message.answer("❌ У вас нет лошади. Купить: /horse buy")
            return
        # Get lootboxer level for max level calculation
        from database.engine import async_session as sess
        from database.models import Profession
        async with sess() as s:
            prof = await s.get(Profession, message.from_user.id)
            lootboxer_level = prof.lootboxer_level if prof else 1
        text = format_horse_info(horse, lootboxer_level)
        await message.answer(text, parse_mode="HTML")
        return

    sub = args[0].lower()

    if sub == "buy":
        if horse:
            await message.answer("❌ У вас уже есть лошадь.")
            return
        from game.horses import BREEDING_TYPES, roll_horse_type
        from game.player import remove_coins

        # Wiki: /buy basic horse costs 500 coins
        cost = 500
        if user.coins < cost:
            await message.answer(f"❌ Нужно {cost} монет.")
            return

        await remove_coins(message.from_user.id, cost)

        # Random type (no special/super_special on first buy)
        htype = random.choice(["normal", "defender", "strong", "tank", "golden", "magic", "festive"])
        types = get_horse_types()

        from database.engine import async_session
        from database.models import Horse as HorseModel

        async with async_session() as s:
            new_horse = HorseModel(
                user_id=message.from_user.id,
                name=f"{types[htype]['name']} Horse",
                horse_type=htype,
                tier=1,
                level=1,
            )
            s.add(new_horse)
            await s.commit()

        await message.answer(f"🐴 Куплена лошадь: {types[htype]['emoji']} {types[htype]['name']}! (-{cost} монет)")
        return

    if sub == "training":
        result = await horse_training(message.from_user.id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    if sub == "breeding":
        if len(args) < 2:
            await message.answer("Формат: /horse breeding @username")
            return
        target_name = args[1].lstrip("@")
        from database.engine import async_session
        from database.models import User
        from sqlalchemy import select

        async with async_session() as s:
            result = await s.execute(select(User).where(User.username == target_name))
            target = result.scalar_one_or_none()
            if not target:
                await message.answer(f"❌ Игрок @{target_name} не найден.")
                return

        result = await horse_breeding(message.from_user.id, target.user_id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    if sub == "race":
        result = await horse_race(message.from_user.id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    if sub == "feed":
        result = await horse_feed(message.from_user.id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    if sub == "epicness":
        result = await horse_epicness(message.from_user.id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    await message.answer(
        "🐴 <b>Команды лошади:</b>\n\n"
        "/horse info — Информация\n"
        "/horse buy [тип] — Купить\n"
        "/horse training — Тренировка\n"
        "/horse breeding @player — Разведение\n"
        "/horse race — Гонки (тир V+)\n"
        "/horse feed — Покормить морковью\n"
        "/horse epicness — EPIC berries\n"
        "/eat horse — \"Регретируй свои слова\"",
        parse_mode="HTML"
    )


@router.message(F.text == "/eat horse")
async def cmd_eat_horse(message: Message):
    """Wiki: 'Regret your words'"""
    await message.answer("🐴 ...Вы пожалели о своих словах. Лошадь смотрит на вас с осуждением.")
