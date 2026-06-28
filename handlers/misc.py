"""Simple utility commands: /rules, /coins, /life"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user

router = Router()


@router.message(F.text == "/rules")
async def cmd_rules(message: Message):
    text = (
        "📜 <b>Правила EPIC RPG</b>\n\n"
        "1. Используй /hunt для охоты на мобов и получения XP/монет\n"
        "2. Используй /adventure для приключений (часовой кулдаун)\n"
        "3. Работай: /chop, /fish, /mine, /pickup для сбора ресурсов\n"
        "4. Крафти снаряжение: /craft\n"
        "5. Улучшай инструменты в/Area Commands\n"
        "6. Прокачивай лошадь: /horse buy, /horse train\n"
        "7. Собирай питомцев: /pets\n"
        "8. Используй Time Travel для перезапуска с бонусами\n"
        "9. Не забывай про кулдауны: /cooldowns\n"
        "10. Играй честно и весело!\n\n"
        "Полезные команды:\n"
        "  /profile — статистика\n"
        "  /inventory — инвентарь\n"
        "  /top — рейтинг\n"
        "  /help — помощь\n"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/coins")
async def cmd_coins(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    text = (
        f"💰 <b>Монеты</b>\n\n"
        f"Кошелёк: {user.coins:,}\n"
        f"Эпические монеты: {user.epic_coins:,}\n"
        f"В банке: {user.bank:,}\n"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/life")
async def cmd_life(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    from game.player import calc_atk, calc_def
    from database.crud import get_equipment
    eq = await get_equipment(message.from_user.id)

    text = (
        f"❤️ <b>Здоровье</b>\n\n"
        f"HP: {user.level * 10} / {user.level * 10}\n"
        f"Уровень: {user.level}\n"
        f"ATK: {calc_atk(user.level, eq.get('weapon_tier', 1))}\n"
        f"DEF: {calc_def(user.level, eq.get('armor_tier', 1))}\n\n"
        f"Зелье жизни: /use life_potion"
    )
    await message.answer(text, parse_mode="HTML")
