"""
Work commands: /chop, /pickup, /mine, /fish + their upgrades.
"""
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, get_cooldowns, update_cooldown
from datetime import datetime
import config

router = Router()


def _check_area(user, area_req: int) -> str | None:
    """Check area requirement. Returns error message or None.
    Ascended players can use commands unlocked in previous runs (max_area >= req)."""
    if user.area >= area_req:
        return None
    if getattr(user, 'ascended', False) and getattr(user, 'max_area', 1) >= area_req:
        return None
    return f"❌ Эта команда доступна с Area {area_req}."


def _check_cooldown(cd, field: str, action: str, user) -> str | None:
    """Check if a cooldown is active. Returns error message or None."""
    now = datetime.utcnow()
    cd_time = getattr(cd, field, None)
    if cd_time and cd_time > datetime.min:
        elapsed = (now - cd_time).total_seconds()
        required = config.COOLDOWNS.get(action, 0)
        if elapsed < required:
            remaining = int(required - elapsed)
            m, s = divmod(remaining, 60)
            return f"⏳ Кулдаун {action}: {m}м {s}с"
    return None


# --- Chop family ---
@router.message(F.text == "/chop")
@router.message(F.text == "/axe")
@router.message(F.text == "/bowsaw")
@router.message(F.text == "/chainsaw")
async def cmd_chop(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    cmd = message.text.lstrip("/").lower()
    area_req = {"chop": 1, "axe": 3, "bowsaw": 6, "chainsaw": 9}.get(cmd, 1)
    err = _check_area(user, area_req)
    if err:
        await message.answer(err)
        return

    if cmd == "chop":
        cd = await get_cooldowns(message.from_user.id)
        err = _check_cooldown(cd, "chop_last", "chop", user)
        if err:
            await message.answer(err)
            return
        await update_cooldown(message.from_user.id, "chop")

    from game.work import chop
    result = await chop(message.from_user.id, cmd=cmd)
    await message.answer(result["message"])

    # Try to spawn Big Chop / Treasure Hunt event
    from game.events import try_spawn_event, resolve_event, EVENT_TYPES, active_events, EVENT_WINDOW
    from utils.keyboards import event_keyboard
    event = await try_spawn_event(message.chat.id, user.area, source="chop")
    if event:
        info = EVENT_TYPES[event["type"]]
        ev_msg = await message.answer(
            f"🌍 <b>{info['label']}!</b>\n"
            f"Участников: 0 | Осталось: {EVENT_WINDOW}с | Минимум: 3\n"
            f"Нажмите кнопку чтобы участвовать!",
            reply_markup=event_keyboard(event["type"]),
            parse_mode="HTML",
        )
        # Store message_id in event for editing
        key = f"{message.chat.id}_{event['type']}"
        if key in active_events:
            active_events[key]["message_id"] = ev_msg.message_id

        # Schedule auto-resolve
        chat_id = message.chat.id
        etype = event["type"]
        async def _auto_resolve(cid=chat_id, et=etype):
            await asyncio.sleep(30)
            result = await resolve_event(cid, et)
            if result:
                await message.answer(result["message"], parse_mode="HTML")
        asyncio.create_task(_auto_resolve())


# --- Fish family ---
@router.message(F.text == "/fish")
@router.message(F.text == "/net")
@router.message(F.text == "/boat")
@router.message(F.text == "/bigboat")
async def cmd_fish(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    cmd = message.text.lstrip("/").lower()
    area_req = {"fish": 1, "net": 3, "boat": 6, "bigboat": 9}.get(cmd, 1)
    if user.area < area_req:
        await message.answer(f"❌ {cmd.title()} доступен с Area {area_req}.")
        return

    if cmd == "fish":
        cd = await get_cooldowns(message.from_user.id)
        err = _check_cooldown(cd, "fish_last", "fish", user)
        if err:
            await message.answer(err)
            return
        await update_cooldown(message.from_user.id, "fish")

    from game.work import fish
    result = await fish(message.from_user.id, cmd=cmd)
    await message.answer(result["message"])


# --- Mine family ---
@router.message(F.text == "/mine")
@router.message(F.text == "/pickaxe")
@router.message(F.text == "/drill")
@router.message(F.text == "/dynamite")
async def cmd_mine(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    cmd = message.text.lstrip("/").lower()
    area_req = {"mine": 5, "pickaxe": 6, "drill": 10, "dynamite": 12}.get(cmd, 5)
    if user.area < area_req:
        await message.answer(f"❌ {cmd.title()} доступен с Area {area_req}.")
        return

    if cmd == "mine":
        cd = await get_cooldowns(message.from_user.id)
        err = _check_cooldown(cd, "mine_last", "mine", user)
        if err:
            await message.answer(err)
            return
        await update_cooldown(message.from_user.id, "mine")

    from game.work import mine
    result = await mine(message.from_user.id, cmd=cmd)
    await message.answer(result["message"])

    # Try to spawn Big Mine event
    from game.events import try_spawn_event, resolve_event, EVENT_TYPES, active_events, EVENT_WINDOW
    from utils.keyboards import event_keyboard
    event = await try_spawn_event(message.chat.id, user.area, source="mine")
    if event:
        info = EVENT_TYPES[event["type"]]
        ev_msg = await message.answer(
            f"🌍 <b>{info['label']}!</b>\n"
            f"Участников: 0 | Осталось: {EVENT_WINDOW}с | Минимум: 3\n"
            f"Нажмите кнопку чтобы участвовать!",
            reply_markup=event_keyboard(event["type"]),
            parse_mode="HTML",
        )
        key = f"{message.chat.id}_{event['type']}"
        if key in active_events:
            active_events[key]["message_id"] = ev_msg.message_id
        # Schedule auto-resolve
        chat_id = message.chat.id
        etype = event["type"]
        async def _auto_resolve(cid=chat_id, et=etype):
            await asyncio.sleep(30)
            result = await resolve_event(cid, et)
            if result:
                await message.answer(result["message"], parse_mode="HTML")
        asyncio.create_task(_auto_resolve())


# --- Pickup family ---
@router.message(F.text == "/pickup")
@router.message(F.text == "/ladder")
@router.message(F.text == "/tractor")
@router.message(F.text == "/greenhouse")
async def cmd_pickup(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    cmd = message.text.lstrip("/").lower()
    area_req = {"pickup": 3, "ladder": 4, "tractor": 8, "greenhouse": 11}.get(cmd, 3)
    if user.area < area_req:
        await message.answer(f"❌ {cmd.title()} доступен с Area {area_req}.")
        return

    if cmd == "pickup":
        cd = await get_cooldowns(message.from_user.id)
        err = _check_cooldown(cd, "chop_last", "pickup", user)
        if err:
            await message.answer(err)
            return
        await update_cooldown(message.from_user.id, "chop")

    from game.work import pickup
    result = await pickup(message.from_user.id, cmd=cmd)
    await message.answer(result["message"])
