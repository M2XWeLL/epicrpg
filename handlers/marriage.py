"""Marriage system: /marry, /divorce, /hunt_together"""
import random
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user
from database.engine import async_session
from database.models import User, Marriage
from sqlalchemy import select, or_

router = Router()


async def get_partner(user_id: int) -> int | None:
    """Return partner user_id or None if not married."""
    async with async_session() as s:
        result = await s.execute(
            select(Marriage).where(
                or_(Marriage.user1_id == user_id, Marriage.user2_id == user_id)
            )
        )
        m = result.scalar_one_or_none()
        if not m:
            return None
        return m.user2_id if m.user1_id == user_id else m.user1_id


@router.message(F.text == "/marry")
async def cmd_marry(message: Message):
    """Marry another player. Usage: /marry @username or reply to their message."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    # Check if already married
    partner_id = await get_partner(message.from_user.id)
    if partner_id:
        partner = await get_partner(partner_id)
        partner_user = await get_user(partner_id)
        name = partner_user.username if partner_user else str(partner_id)
        await message.answer(f"❌ Вы уже женаты на {name}. Сначала /divorce")
        return

    # Get target: reply or @mention
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split()[1:]
        if args:
            # Try to find by username (simplified - in real bot would need DB lookup)
            await message.answer(
                "💡 Ответьте на сообщение игрока командой /marry\n"
                "Или используйте /marry [user_id]"
            )
            return
        else:
            await message.answer(
                "Формат: ответьте на сообщение игрока /marry\n"
                "Или: /marry [user_id]"
            )
            return

    if target_id == message.from_user.id:
        await message.answer("❌ Нельзя жениться на себе!")
        return

    target = await get_user(target_id)
    if not target:
        await message.answer("❌ Этот пользователь не зарегистрирован.")
        return

    # Check if target is already married
    target_partner = await get_partner(target_id)
    if target_partner:
        await message.answer(f"❌ {target.username or target_id} уже в браке.")
        return

    # Marriage cost: 10000 coins
    cost = 10000
    if user.coins < cost:
        await message.answer(f"❌ Для свадьбы нужно {cost:,} монет. У вас: {user.coins:,}")
        return

    # Deduct cost and create marriage
    async with async_session() as s:
        u = await s.get(User, message.from_user.id)
        u.coins -= cost
        marriage = Marriage(user1_id=message.from_user.id, user2_id=target_id)
        s.add(marriage)
        await s.commit()

    name1 = user.username or str(message.from_user.id)
    name2 = target.username or str(target_id)
    await message.answer(
        f"💍 <b>Свадьба!</b>\n\n"
        f"{name1} 💕 {name2}\n\n"
        f"Поздравляем! Теперь вы можете:\n"
        f"  /hunt_together — охота вдвоём\n"
        f"  /divorce — развестись"
    )


@router.message(F.text == "/divorce")
async def cmd_divorce(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    partner_id = await get_partner(message.from_user.id)
    if not partner_id:
        await message.answer("❌ Вы не в браке.")
        return

    partner_user = await get_user(partner_id)
    partner_name = partner_user.username if partner_user else str(partner_id)

    async with async_session() as s:
        result = await s.execute(
            select(Marriage).where(
                or_(Marriage.user1_id == message.from_user.id,
                    Marriage.user2_id == message.from_user.id)
            )
        )
        m = result.scalar_one_or_none()
        if m:
            await s.delete(m)
            await s.commit()

    my_name = user.username or str(message.from_user.id)
    await message.answer(
        f"💔 <b>Развод</b>\n\n"
        f"{my_name} и {partner_name} больше не вместе.\n"
        f"Оба партнёра потеряли 500 монет.\n\n"
        f"Удачи в поисках новой любви!"
    )

    # Both lose 500 coins
    async with async_session() as s:
        u1 = await s.get(User, message.from_user.id)
        u2 = await s.get(User, partner_id)
        if u1:
            u1.coins = max(0, u1.coins - 500)
        if u2:
            u2.coins = max(0, u2.coins - 500)
        await s.commit()


@router.message(F.text == "/hunt_together")
async def cmd_hunt_together(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    partner_id = await get_partner(message.from_user.id)
    if not partner_id:
        await message.answer(
            "❌ Вы не в браке.\n"
            "Используй /marry чтобы найти партнёра."
        )
        return

    partner = await get_user(partner_id)
    if not partner:
        await message.answer("❌ Ваш партнёр не найден в базе.")
        return

    from database.crud import update_cooldown
    allowed, remaining = await update_cooldown(message.from_user.id, "hunt")
    if not allowed:
        mins, secs = divmod(remaining, 60)
        await message.answer(f"⏳ Кулдаун: {mins}м {secs}с")
        return

    # Partner gets separate cooldown check
    allowed2, remaining2 = await update_cooldown(partner_id, "hunt")
    if not allowed2:
        mins, secs = divmod(remaining2, 60)
        await message.answer(
            f"❌ Ваш партнёр на кулдауне ({mins}м {secs}с).\n"
            f"Попробуйте позже или используйте /hunt в одиночку."
        )
        return

    from game.player import calc_atk, calc_def
    eq1 = await get_equipment(message.from_user.id)
    eq2 = await get_equipment(partner_id)
    atk1 = calc_atk(user.level, eq1.get("weapon_tier", 1))
    atk2 = calc_atk(partner.level, eq2.get("weapon_tier", 1))
    total_atk = atk1 + atk2

    # Stronger mobs for duo
    area = min(user.area, partner.area)
    from config import AREA_MOBS
    mobs = AREA_MOBS.get(area, AREA_MOBS[1])
    mob = random.choice(mobs)
    mob["hp"] = int(mob["hp"] * 1.8)
    mob["atk"] = int(mob["atk"] * 1.5)

    # Combat
    mob_hp = mob["hp"]
    dmg = max(1, total_atk + random.randint(-total_atk // 4, total_atk // 4))
    mob_hp -= dmg

    won = mob_hp <= 0

    if won:
        import math
        xp_each = int(mob["xp"] * 0.8)
        coins_each = int(mob["coins"] * 0.8)

        from game.player import add_xp, add_coins
        await add_xp(message.from_user.id, xp_each)
        await add_xp(partner_id, xp_each)
        await add_coins(message.from_user.id, coins_each)
        await add_coins(partner_id, coins_each)

        drop_text = ""
        if "drop" in mob and random.random() < mob["drop"].get("chance", 0) * 1.5:
            from database.crud import add_materials
            add_materials(message.from_user.id, mob["drop"]["item"], 1)
            add_materials(partner_id, mob["drop"]["item"], 1)
            drop_text = f"\n🎁 Оба получили: {mob['drop']['item']}"

        p1 = user.username or str(message.from_user.id)
        p2 = partner.username or str(partner_id)
        await message.answer(
            f"💕 <b>Охота вдвоём — Победа!</b>\n\n"
            f"{p1} + {p2}\n"
            f"{mob['emoji']} {mob['name']}: -{dmg} HP\n\n"
            f"Награда каждому:\n"
            f"  ⭐ {xp_each} XP | 💰 {coins_each} монет"
            f"{drop_text}"
        )
    else:
        p1 = user.username or str(message.from_user.id)
        p2 = partner.username or str(partner_id)
        await message.answer(
            f"💕 <b>Охота вдвоём — Поражение</b>\n\n"
            f"{p1} + {p2}\n"
            f"{mob['emoji']} {mob['name']}: {mob_hp} HP осталось\n\n"
            f"В следующий раз повезёт!"
        )
