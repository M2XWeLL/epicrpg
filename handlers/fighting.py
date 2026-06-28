"""
Fighting commands: duel, arena, miniboss, heal.
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, get_cooldowns, get_inventory, remove_materials
from database.engine import async_session
from database.models import Cooldown
from game.arena import duel_fight, arena_fight, miniboss_fight
from game.player import add_coins
from datetime import datetime
import config

router = Router()


@router.message(F.text.startswith("/duel"))
async def cmd_duel(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if not args:
        await message.answer("Формат: /duel @username")
        return

    target_name = args[0].lstrip("@")

    from database.engine import async_session as sess
    from database.models import User
    from sqlalchemy import select

    async with sess() as s:
        result = await s.execute(select(User).where(User.username == target_name))
        target = result.scalar_one_or_none()
        if not target:
            await message.answer(f"❌ Игрок @{target_name} не найден.")
            return
        if target.user_id == message.from_user.id:
            await message.answer("❌ Нельзя дуэлиться с собой.")
            return

    # Check cooldown
    cd = await get_cooldowns(message.from_user.id)
    now = datetime.utcnow()
    if cd.last_duel and (now - cd.last_duel).total_seconds() < config.COOLDOWNS["duel"]:
        remaining = config.COOLDOWNS["duel"] - int((now - cd.last_duel).total_seconds())
        await message.answer(f"⏳ Кулдаун дуэли: {remaining}с")
        return

    # Set cooldown
    async with async_session() as s:
        cd_obj = await s.get(Cooldown, message.from_user.id)
        if cd_obj:
            cd_obj.last_duel = now
            await s.commit()

    result = await duel_fight(message.from_user.id, target.user_id)
    if not result["success"]:
        await message.answer(result["message"])
        return

    text = f"⚔️ <b>Дуэль</b>\n\n"
    text += result["log"]
    if result["victory"]:
        text += f"\n\n🎉 {result['winner']} побеждает! +{result['coins']} монет"
    else:
        text += f"\n\n🎉 {result['winner']} побеждает! +{result['coins']} монет"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/arena")
async def cmd_arena(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    cd = await get_cooldowns(message.from_user.id)
    now = datetime.utcnow()
    if cd.last_arena and (now - cd.last_arena).total_seconds() < config.COOLDOWNS["arena"]:
        remaining = config.COOLDOWNS["arena"] - int((now - cd.last_arena).total_seconds())
        await message.answer(f"⏳ Кулдаун арены: {remaining}с")
        return

    async with async_session() as s:
        cd_obj = await s.get(Cooldown, message.from_user.id)
        if cd_obj:
            cd_obj.last_arena = now
            await s.commit()

    result = await arena_fight(message.from_user.id)
    text = result["log"]
    if result["victory"]:
        text += f"\n\n🎉 Победа! +{result['coins']} монет, +{result['xp']} XP"
    else:
        text += "\n\n💀 Поражение!"
    await message.answer(text)

    # Quest hook — joining arena counts
    from game.quest import on_arena_join
    await on_arena_join(message.from_user.id)


@router.message(F.text == "/miniboss")
async def cmd_miniboss(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    result = await miniboss_fight(message.from_user.id)
    text = result["log"]
    if result["victory"]:
        text += f"\n\n🎉 Победа! +{result['coins']} монет, +{result['xp']} XP"
        # Quest hook — miniboss kill
        from game.quest import on_miniboss_kill
        await on_miniboss_kill(message.from_user.id)
    else:
        text += "\n\n💀 Поражение!"
    await message.answer(text)


@router.message(F.text == "/heal")
async def cmd_heal(message: Message):
    """Heal with life potion — restore to full HP. Wiki: costs 25 coins to buy."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    max_hp = 100 + user.level * 5

    # Wiki: cannot heal if at max HP
    if user.current_hp >= max_hp:
        await message.answer(f"❤️ У вас полное HP: {max_hp}/{max_hp}")
        return

    # Wiki: cannot heal if life boost is active
    if user.life_boost_active:
        await message.answer("❌ Нельзя лечиться пока активен Life Boost!")
        return

    inv = await get_inventory(message.from_user.id)
    potions = inv.get("life_potion", 0)
    if potions <= 0:
        await message.answer(
            f"❌ У вас нет зелий жизни.\n"
            f"Купить: /buy life_potion 25 монет\n"
            f"HP: {user.current_hp}/{max_hp}"
        )
        return

    await remove_materials(message.from_user.id, "life_potion", 1)

    # Restore HP to full
    from database.models import User
    async with async_session() as s:
        u = await s.get(User, message.from_user.id)
        if u:
            u.current_hp = max_hp
            await s.commit()

    await message.answer(
        f"🧪 <b>Лечение</b>\n\n"
        f"HP: {user.current_hp} → {max_hp}/{max_hp}\n"
        f"🧪 Зелий осталось: {potions - 1}",
        parse_mode="HTML"
    )
