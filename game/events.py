"""Regular Events — Big Chop, Big Mine, Treasure Hunt.

Triggered randomly during /chop or /mine.
Duration: 30 seconds. Min players: 3.
All participants receive fixed rewards per wiki.
"""
import asyncio
import random
import json
import config
from datetime import datetime, timezone, timedelta

# Active events cache (in-memory, per process)
active_events = {}

EVENT_WINDOW = 30  # seconds
EVENT_MIN_PLAYERS = 3

# Big Chop: triggered by /chop
BIG_CHOP_REWARDS = {
    "wooden_log": 400,
    "epic_log": 20,
    "super_log": 50,
    "mega_log": 200,
    "hyper_log": 250,
    "ultra_log": 100,
}

# Big Mine: triggered by /mine
BIG_MINE_REWARDS = {
    "ruby": 50,
    "diamond": 20,
    "amber": 100,
    "emerald": 200,
    "sapphire": 250,
}

# Treasure Hunt: triggered by /chop (rare)
TREASURE_HUNT_REWARDS = {
    "coin": 1000000,       # 1M coins
    "edgy_lootbox": 2,
    "arenacookie": 1000,
}
# EPIC Coins are a special currency, handled separately

EVENT_TYPES = {
    "big_chop": {
        "spawn_chance": 0.05,
        "emoji": "🪓",
        "label": "Большая рубка",
        "button": "🪓 РУБИТЬ!",
        "rewards": BIG_CHOP_REWARDS,
        "epic_coins_reward": 0,
    },
    "big_mine": {
        "spawn_chance": 0.05,
        "emoji": "⛏️",
        "label": "Большая копь",
        "button": "⛏️ КОПАТЬ!",
        "rewards": BIG_MINE_REWARDS,
        "epic_coins_reward": 0,
    },
    "treasure_hunt": {
        "spawn_chance": 0.03,
        "emoji": "🗺️",
        "label": "Поиск сокровищ",
        "button": "🗺️ ИСКАТЬ!",
        "rewards": TREASURE_HUNT_REWARDS,
        "epic_coins_reward": 5,
    },
}


async def try_spawn_event(chat_id: int, area: int, source: str = "chop") -> dict | None:
    """Try to spawn a random event. Called after chop/mine commands.

    source: 'chop' or 'mine' — determines which events can spawn.
    """
    possible = []
    for event_type, info in EVENT_TYPES.items():
        if source == "chop" and event_type in ("big_chop", "treasure_hunt"):
            possible.append((event_type, info))
        elif source == "mine" and event_type == "big_mine":
            possible.append((event_type, info))

    for event_type, info in possible:
        if random.random() < info["spawn_chance"]:
            key = f"{chat_id}_{event_type}"
            if key in active_events:
                continue

            event = {
                "type": event_type,
                "chat_id": chat_id,
                "area": area,
                "started_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=EVENT_WINDOW),
                "clicks": set(),
                "message_id": None,  # set by handler after sending
            }
            active_events[key] = event
            return event

    return None


async def handle_event_click(chat_id: int, event_type: str, user_id: int) -> dict:
    """Handle a click on event button."""
    key = f"{chat_id}_{event_type}"
    event = active_events.get(key)
    if not event:
        return {"success": False, "message": "Ивент уже завершён."}

    if datetime.now(timezone.utc) > event["expires_at"]:
        del active_events[key]
        return {"success": False, "message": "Ивент уже завершён."}

    if user_id in event["clicks"]:
        return {"success": False, "message": "Вы уже нажали кнопку!"}

    event["clicks"].add(user_id)
    return {"success": True, "message": f"✅ Вы присоединились! Участников: {len(event['clicks'])}"}


async def resolve_event(chat_id: int, event_type: str) -> dict | None:
    """Resolve event after timer expires. Gives rewards to all participants."""
    key = f"{chat_id}_{event_type}"
    event = active_events.pop(key, None)
    if not event:
        return None

    participants = list(event["clicks"])
    count = len(participants)

    if count < EVENT_MIN_PLAYERS:
        return {
            "success": False,
            "message": f"❌ Ивент провален! Нужно минимум {EVENT_MIN_PLAYERS} участников (было: {count}).",
        }

    info = EVENT_TYPES[event_type]
    rewards = info["rewards"]

    from database.crud import add_materials
    from database.engine import async_session
    from database.models import User

    for uid in participants:
        for mat, amount in rewards.items():
            await add_materials(uid, mat, amount)
        # EPIC coins reward
        epic = info.get("epic_coins_reward", 0)
        if epic > 0:
            async with async_session() as s:
                user = await s.get(User, uid)
                if user:
                    user.epic_coins += epic
                    await s.commit()

    # Format reward summary
    reward_lines = []
    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    mat_names = mat_data.get("names", {})
    mat_emojis = mat_data.get("emojis", {})
    for mat, amount in rewards.items():
        emoji = mat_emojis.get(mat, "❓")
        name = mat_names.get(mat, mat)
        reward_lines.append(f"  {emoji} {amount:,}x {name}")
    epic = info.get("epic_coins_reward", 0)
    if epic > 0:
        reward_lines.append(f"  💎 {epic} EPIC Coins")

    return {
        "success": True,
        "type": event_type,
        "participants": count,
        "message": (
            f"{info['emoji']} <b>{info['label']} завершён!</b>\n"
            f"{count} участников получили:\n"
            + "\n".join(reward_lines)
        ),
    }


def get_active_event(chat_id: int, event_type: str) -> dict | None:
    """Get an active event if it exists and hasn't expired."""
    key = f"{chat_id}_{event_type}"
    event = active_events.get(key)
    if not event:
        return None
    if datetime.now(timezone.utc) > event["expires_at"]:
        del active_events[key]
        return None
    return event
