"""Cosmetic and world commands: /bg, /world"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user

router = Router()

BACKGROUNDS = {
    "forest": {"emoji": "🌲", "name": "Лес", "cost": 5000},
    "dungeon": {"emoji": "🏰", "name": "Подземелье", "cost": 10000},
    "ocean": {"emoji": "🌊", "name": "Океан", "cost": 7500},
    "volcano": {"emoji": "🌋", "name": "Вулкан", "cost": 15000},
    "sky": {"emoji": "☁️", "name": "Небо", "cost": 3000},
    "night": {"emoji": "🌙", "name": "Ночь", "cost": 4000},
    "space": {"emoji": "🌌", "name": "Космос", "cost": 20000},
    "crystal": {"emoji": "💎", "name": "Кристаллы", "cost": 25000},
}

# Track last world event for /world
_world_state = {
    "current_event": None,
    "event_started": None,
    "event_bonus": None,
}


@router.message(F.text == "/bg")
@router.message(F.text.startswith("/bg "))
async def cmd_bg(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:]

    if not args:
        # Show available backgrounds
        text = "🎨 <b>Фоны профиля</b>\n\n"
        for key, bg in BACKGROUNDS.items():
            text += f"  {bg['emoji']} {bg['name']} ({key}) — 💰 {bg['cost']:,}\n"
        text += (
            "\nКупить: /bg [название]\n"
            f"Ваш фон: {user.title or 'нет'}"
        )
        await message.answer(text, parse_mode="HTML")
        return

    bg_name = args[0].lower()
    if bg_name not in BACKGROUNDS:
        await message.answer("❌ Неизвестный фон. Используй /bg для списка.")
        return

    bg = BACKGROUNDS[bg_name]
    if user.coins < bg["cost"]:
        await message.answer(f"❌ Недостаточно монет. Нужно: {bg['cost']:,}")
        return

    from database.engine import async_session
    from database.models import User
    async with async_session() as s:
        u = await s.get(User, message.from_user.id)
        u.coins -= bg["cost"]
        u.title = f"{bg['emoji']} {bg['name']}"
        await s.commit()

    await message.answer(f"🎨 Фон изменён на {bg['emoji']} {bg['name']}!")


@router.message(F.text == "/world")
async def cmd_world(message: Message):
    """Show current world state and events."""
    import random
    import datetime as _dt

    now = _dt.datetime.utcnow()
    hour = now.hour

    # Determine time of day
    if 6 <= hour < 12:
        time_name = "☀️ Утро"
    elif 12 <= hour < 18:
        time_name = "🌤️ День"
    elif 18 <= hour < 22:
        time_name = "🌅 Вечер"
    else:
        time_name = "🌙 Ночь"

    # Random world events
    events = [
        "🟡 Торговец странствует по мирам ( bonuses на sell +20%)",
        "🔴 Босс появился в подземелье! (/dungeon для挑战)",
        "🟢 Фестиваль урожая (work rewards x2)",
        "🔵 Метеоритный дождь (chance на rare items +50%)",
        "🟣 Тёмный портал открыт (adventure rewards x1.5)",
        "⚪ Мирный день (все кулдауны -30%)",
    ]

    # Pick event based on current minute (stable for ~5 min)
    event_idx = (now.minute // 5) % len(events)
    event = events[event_idx]

    text = (
        f"🌍 <b>Мир Epic RPG</b>\n\n"
        f"Время: {time_name}\n\n"
        f"Текущее событие:\n  {event}\n\n"
        f"Мировые статусы:\n"
        f"  🏪 Магазин: открыт\n"
        f"  ⚒️ Кузнец: работает\n"
        f"  🌾 Ферма: доступна\n"
        f"  🏛️ Арена: открыта\n"
        f"  🎰 Казино: работает\n"
    )
    await message.answer(text, parse_mode="HTML")
