"""
Quest system — wiki-accurate implementation.
Quest types: hunt, adventure, craft, gambling, arena, miniboss, cooking, guild, trading.
Quest progress is tracked via hooks called from other game modules.
"""
import random
from datetime import datetime, timedelta
from database.crud import get_user, add_materials, add_profession_xp
from database.engine import async_session
from database.models import User
import config


# Quest display names (Russian)
QUEST_NAMES = {
    "hunt":      "Охота",
    "adventure": "Приключение",
    "craft":     "Крафт",
    "gambling":  "Азарт",
    "arena":     "Арена",
    "miniboss":  "Мини-босс",
    "cooking":   "Готовка",
    "guild":     "Гильдия",
    "trading":   "Торговля",
}


async def generate_quest(user_id: int) -> dict:
    """Generate a new quest for the user. Returns quest info dict."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    # Check 6h cooldown
    now = datetime.utcnow()
    assigned = user.quest_assigned_at
    if assigned and assigned.tzinfo is not None:
        assigned = assigned.replace(tzinfo=None)
    if assigned and (now - assigned).total_seconds() < config.QUEST_COOLDOWN:
        remaining = int(config.QUEST_COOLDOWN - (now - assigned).total_seconds())
        hours, rem = divmod(remaining, 3600)
        mins = rem // 60
        return {"success": False, "message": f"⏳ Квест будет доступен через {hours}ч {mins}м."}

    # Check decline cooldown
    cooldown_until = user.quest_cooldown_until
    if cooldown_until and cooldown_until.tzinfo is not None:
        cooldown_until = cooldown_until.replace(tzinfo=None)
    if cooldown_until and now < cooldown_until:
        remaining = int((cooldown_until - now).total_seconds())
        mins = remaining // 60
        return {"success": False, "message": f"⏳ Подождите {mins}м перед новым квестом."}

    # Determine available quest types based on max_area
    available = []
    for area_req, types in config.QUEST_TYPES_BY_AREA.items():
        if user.max_area >= area_req:
            available.extend(types)
    if not available:
        available = ["hunt", "adventure", "craft", "gambling", "arena", "miniboss", "trading"]

    quest_type = random.choice(available)
    qdef = config.QUEST_DEFS[quest_type]

    # Generate quest specifics
    target = qdef["target"]
    mob_name = ""
    material_name = ""
    gambling_target = 0

    if quest_type in ("hunt", "adventure"):
        # Pick a random mob from highest area
        from config import AREA_MOBS
        mob_pool = AREA_MOBS.get(user.max_area, AREA_MOBS.get(1))
        mob = random.choice(mob_pool)
        mob_name = mob["name"]
    elif quest_type == "craft":
        # Pick a random material available at user's max area
        mat_pool = _materials_for_area(user.max_area)
        material_name = random.choice(mat_pool)
        target = max(1, random.randint(1, 3))
    elif quest_type == "gambling":
        gambling_target = user.level * random.randint(50, 200)
        target = gambling_target

    # Calculate rewards
    coin_reward = int(user.level * 100 * qdef["coin_mult"])
    xp_reward = int(user.level * 50 * qdef["xp_mult"])
    item_reward = qdef["item"]
    item_amount = max(1, qdef["item_base"] + user.max_area // 3)

    # Save to DB
    async with async_session() as s:
        u = await s.get(User, user_id)
        if not u:
            return {"success": False, "message": "Игрок не найден."}
        u.current_quest = quest_type
        u.quest_type = quest_type
        u.quest_mob = mob_name
        u.quest_material = material_name
        u.quest_target = target
        u.quest_progress = 0
        u.quest_reward = coin_reward
        u.quest_completed = False
        u.quest_item_reward = item_reward
        u.quest_item_reward_amount = item_amount
        u.quest_coins_reward = coin_reward
        u.quest_xp_reward = xp_reward
        u.quest_assigned_at = now
        await s.commit()

    # Format quest message
    quest_name = QUEST_NAMES.get(quest_type, quest_type)
    desc = _quest_description(quest_type, mob_name, material_name, target, gambling_target)

    return {
        "success": True,
        "message": (
            f"📜 <b>Новый квест: {quest_name}</b>\n\n"
            f"{desc}\n\n"
            f"💰 Награда: {coin_reward:,} монет\n"
            f"⭐ Награда: {xp_reward} XP\n"
            f"🎁 Бонус: {item_amount}x {_item_name(item_reward)}\n\n"
            f"Проверить прогресс: /quest\n"
            f"Бросить квест: /quest quit"
        ),
    }


def _quest_description(quest_type, mob_name, material_name, target, gambling_target):
    """Generate quest description text."""
    if quest_type == "hunt":
        return f"Убить 3x {mob_name} на охоте"
    elif quest_type == "adventure":
        return f"Убить 1x {mob_name} в приключении"
    elif quest_type == "craft":
        return f"Скрафтить {target}x {_item_name(material_name)}"
    elif quest_type == "gambling":
        return f"Выиграть {gambling_target:,} монет в любой азартной игре"
    elif quest_type == "arena":
        return "Присоединиться к арене"
    elif quest_type == "miniboss":
        return "Призвать и убить мини-босса"
    elif quest_type == "cooking":
        return f"Приготовить блюдо {target} раз"
    elif quest_type == "guild":
        return "Начать рейд гильдии"
    elif quest_type == "trading":
        return "Совершить сделку с EPIC NPC"
    return "Выполнить задание"


def _materials_for_area(area: int) -> list:
    """Return list of craftable material IDs available at given area."""
    mats = ["wooden_log", "epic_log"]
    if area >= 2:
        mats.append("super_log")
    if area >= 4:
        mats.append("mega_log")
    if area >= 6:
        mats.append("hyper_log")
    if area >= 9:
        mats.extend(["ultra_log", "ultimate_log"])
    if area >= 3:
        mats.extend(["apple", "banana"])
    if area >= 5:
        mats.extend(["ruby", "unicornhorn", "mermaid_hair"])
    if area >= 7:
        mats.append("normie_fish")
    if area >= 9:
        mats.append("chip")
    return mats


def _item_name(item_id):
    """Get display name for an item."""
    try:
        import json
        with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("names", {}).get(item_id, item_id.replace("_", " ").title())
    except Exception:
        return item_id.replace("_", " ").title()


async def get_quest_status(user_id: int) -> dict:
    """Get current quest progress message."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    if not user.quest_type:
        return {"success": True, "has_quest": False, "message": "📜 У вас нет активного квеста.\n\nНачать: /quest start"}

    quest_type = user.quest_type
    quest_name = QUEST_NAMES.get(quest_type, quest_type)
    desc = _quest_description(quest_type, user.quest_mob, user.quest_material, user.quest_target, 0)

    progress = user.quest_progress
    target = user.quest_target

    if user.quest_completed:
        return {
            "success": True,
            "has_quest": True,
            "completed": True,
            "message": (
                f"📜 <b>{quest_name}</b> — ГОТОВО!\n\n"
                f"{desc}\n"
                f"✅ {progress}/{target}\n\n"
                f"Забрать награду: /quest claim"
            ),
        }

    return {
        "success": True,
        "has_quest": True,
        "completed": False,
        "message": (
            f"📜 <b>{quest_name}</b>\n\n"
            f"{desc}\n"
            f"📊 Прогресс: {progress}/{target}\n\n"
            f"Бросить: /quest quit"
        ),
    }


async def claim_quest(user_id: int) -> dict:
    """Claim quest reward after completion."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    if not user.quest_type:
        return {"success": False, "message": "📜 У вас нет активного квеста."}

    if not user.quest_completed:
        progress = user.quest_progress
        target = user.quest_target
        return {"success": False, "message": f"❌ Квест ещё не выполнен! Прогресс: {progress}/{target}"}

    # Give rewards
    quest_type = user.quest_type
    quest_name = QUEST_NAMES.get(quest_type, quest_type)
    coin_reward = user.quest_coins_reward
    xp_reward = user.quest_xp_reward
    item_reward = user.quest_item_reward
    item_amount = user.quest_item_reward_amount

    from game.player import add_coins, add_xp
    await add_coins(user_id, coin_reward)
    await add_xp(user_id, xp_reward)

    if item_reward and item_amount > 0:
        await add_materials(user_id, item_reward, item_amount)

    # Enchanter profession XP (101+: chance to get coins back)
    from database.crud import get_profession_bonus
    prof = await get_profession_bonus(user_id, "enchanter")
    if prof.get("level", 1) >= 101:
        import math
        bonus_chance = 0.02 + math.log10(prof["level"] - 100) * 0.02
        if random.random() < bonus_chance:
            bonus_coins = int(coin_reward * 0.5)
            await add_coins(user_id, bonus_coins)
            coin_reward += bonus_coins

    # Clear quest
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.quest_type = ""
            u.quest_mob = ""
            u.quest_material = ""
            u.quest_target = 0
            u.quest_progress = 0
            u.quest_reward = 0
            u.quest_completed = False
            u.quest_item_reward = ""
            u.quest_item_reward_amount = 0
            u.quest_coins_reward = 0
            u.quest_xp_reward = 0
            await s.commit()

    # Quest profession XP
    await add_profession_xp(user_id, "merchant", 50)

    return {
        "success": True,
        "message": (
            f"📜 <b>{quest_name} выполнен!</b>\n\n"
            f"💰 +{coin_reward:,} монет\n"
            f"⭐ +{xp_reward} XP"
            + (f"\n🎁 +{item_amount}x {_item_name(item_reward)}" if item_reward else "")
        ),
    }


async def quit_quest(user_id: int) -> dict:
    """Quit current quest and set 1h cooldown."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    if not user.quest_type:
        return {"success": False, "message": "📜 У вас нет активного квеста."}

    cooldown_until = datetime.utcnow() + timedelta(seconds=config.QUEST_DECLINE_COOLDOWN)

    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.quest_type = ""
            u.quest_mob = ""
            u.quest_material = ""
            u.quest_target = 0
            u.quest_progress = 0
            u.quest_reward = 0
            u.quest_completed = False
            u.quest_item_reward = ""
            u.quest_item_reward_amount = 0
            u.quest_coins_reward = 0
            u.quest_xp_reward = 0
            u.quest_cooldown_until = cooldown_until
            await s.commit()

    return {"success": True, "message": "❌ Квест брошен. Новый квест будет доступен через 1 час."}


async def check_dungeon_cancel(user_id: int) -> str | None:
    """Auto-cancel quest on dungeon clear. Returns cancel message or None."""
    user = await get_user(user_id)
    if not user or not user.quest_type:
        return None

    # Wiki: clearing a dungeon cancels active quest
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.quest_type = ""
            u.quest_mob = ""
            u.quest_material = ""
            u.quest_target = 0
            u.quest_progress = 0
            u.quest_reward = 0
            u.quest_completed = False
            u.quest_item_reward = ""
            u.quest_item_reward_amount = 0
            u.quest_coins_reward = 0
            u.quest_xp_reward = 0
            await s.commit()

    return "📜 Квест автоматически отменён (прохождение подземелья)."


# ---------------------------------------------------------------------------
# Quest progress hooks — called from other game modules
# ---------------------------------------------------------------------------

async def _update_progress(user_id: int, amount: int = 1) -> bool:
    """Update quest progress. Returns True if quest just completed."""
    user = await get_user(user_id)
    if not user or not user.quest_type or user.quest_completed:
        return False

    new_progress = user.quest_progress + amount
    completed = new_progress >= user.quest_target

    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.quest_progress = new_progress
            if completed:
                u.quest_completed = True
            await s.commit()

    return completed


async def on_hunt_kill(user_id: int, mob_name: str = ""):
    """Called after a successful hunt kill."""
    user = await get_user(user_id)
    if not user or user.quest_type != "hunt" or user.quest_completed:
        return
    # Combat system doesn't track mob names — any hunt kill counts
    await _update_progress(user_id)


async def on_adventure_kill(user_id: int, mob_name: str = ""):
    """Called after a successful adventure kill."""
    user = await get_user(user_id)
    if not user or user.quest_type != "adventure" or user.quest_completed:
        return
    # Combat system doesn't track mob names — any adventure kill counts
    await _update_progress(user_id)


async def on_craft(user_id: int, material: str = "", amount: int = 1):
    """Called after a successful craft."""
    user = await get_user(user_id)
    if not user or user.quest_type != "craft" or user.quest_completed:
        return
    # Any craft counts toward craft quests
    await _update_progress(user_id)


async def on_gambling_win(user_id: int, coins_won: int):
    """Called after winning coins from any gambling command."""
    user = await get_user(user_id)
    if not user or user.quest_type != "gambling" or user.quest_completed:
        return
    await _update_progress(user_id, coins_won)


async def on_arena_join(user_id: int):
    """Called after joining any arena."""
    user = await get_user(user_id)
    if not user or user.quest_type != "arena" or user.quest_completed:
        return
    await _update_progress(user_id)


async def on_miniboss_kill(user_id: int):
    """Called after defeating a miniboss."""
    user = await get_user(user_id)
    if not user or user.quest_type != "miniboss" or user.quest_completed:
        return
    await _update_progress(user_id)


async def on_cook(user_id: int, recipe_name: str = ""):
    """Called after a successful cook."""
    user = await get_user(user_id)
    if not user or user.quest_type != "cooking" or user.quest_completed:
        return
    await _update_progress(user_id)


async def on_guild_raid(user_id: int):
    """Called after starting a guild raid."""
    user = await get_user(user_id)
    if not user or user.quest_type != "guild" or user.quest_completed:
        return
    await _update_progress(user_id)


async def on_npc_trade(user_id: int):
    """Called after trading with EPIC NPC."""
    user = await get_user(user_id)
    if not user or user.quest_type != "trading" or user.quest_completed:
        return
    await _update_progress(user_id)


# ---------------------------------------------------------------------------
# Epic Quest — requires Special or Super Special horse
# ---------------------------------------------------------------------------

async def epic_quest_start(user_id: int, waves: int) -> dict:
    """Start an epic quest with chosen wave count."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    # Check 24h cooldown
    now = datetime.utcnow()
    last = user.epic_quest_last
    if last and last.tzinfo is not None:
        last = last.replace(tzinfo=None)
    if last and (now - last).total_seconds() < 86400:
        remaining = int(86400 - (now - last).total_seconds())
        hours, rem = divmod(remaining, 3600)
        mins = rem // 60
        return {"success": False, "message": f"⏳ Эпический квест будет доступен через {hours}ч {mins}м."}

    # Check horse type
    from database.crud import get_user as _get_user
    from database.engine import async_session as _sess
    async with _sess() as s:
        from database.models import Horse
        horse = await s.get(Horse, user_id)
        if not horse:
            return {"success": False, "message": "❌ У вас нет лошади!"}

        horse_type = horse.horse_type
        if horse_type not in ("special", "super_special"):
            return {"success": False, "message": "❌ Эпический квест требует Special или Super Special лошадь!"}

        max_waves = 15 if horse_type == "special" else 100
        if waves < 1 or waves > max_waves:
            return {"success": False, "message": f"❌ Количество волн: 1-{max_waves} (у вас {horse_type})"}

        u = await s.get(User, user_id)
        if u:
            u.epic_quest_wave = waves
            u.epic_quest_last = now
            await s.commit()

    return {"success": True, "waves": waves, "message": f"⚔️ Эпический квест: {waves} волн!"}


async def epic_quest_fight(user_id: int, chosen_waves: int) -> dict:
    """Run the epic quest fight."""
    import math
    from game.player import calc_atk, calc_def

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    eq_data = await _get_equipment_dict(user_id)
    weapon_tier = eq_data.get("weapon_tier", 1)
    armor_tier = eq_data.get("armor_tier", 1)
    weapon_enchant = eq_data.get("sword_enchant", {}).get("bonus_pct", 0)
    armor_enchant = eq_data.get("armor_enchant", {}).get("bonus_pct", 0)

    player_atk = calc_atk(user.level, weapon_tier, weapon_enchant)
    player_def = calc_def(user.level, armor_tier, armor_enchant)
    player_hp = 100 + user.level * 5

    log = []
    waves_defeated = 0

    for wave in range(1, chosen_waves + 1):
        # Progressive scaling: each wave gets stronger
        wave_mult = 1 + (wave - 1) * 0.15
        mob_hp = int(user.level * 50 * wave_mult)
        mob_atk = int(user.level * 8 * wave_mult)
        mob_def = int(user.level * 3 * wave_mult)

        log.append(f"🌊 Волна {wave}: HP {mob_hp}, ATK {mob_atk}, DEF {mob_def}")

        # Simple fight resolution
        rounds = 0
        while player_hp > 0 and mob_hp > 0 and rounds < 20:
            rounds += 1
            # Player attacks
            dmg = max(1, math.floor((player_atk - mob_def / 2) * random.uniform(0.9, 1.1)))
            mob_hp -= dmg
            if mob_hp <= 0:
                break
            # Monster attacks
            dmg2 = max(1, math.floor((mob_atk - player_def / 2) * random.uniform(0.9, 1.1)))
            player_hp -= dmg2

        if mob_hp <= 0:
            waves_defeated += 1
            log.append(f"  ✅ Победа!")
        else:
            log.append(f"  ❌ Поражение!")
            break

    # Check if player survived
    if player_hp <= 0:
        # Horse saves from death regardless of tier — no rewards
        result_msg = (
            f"⚔️ Эпический квест завершён!\n"
            f"Пройдено волн: {waves_defeated}/{chosen_waves}\n\n"
            f"🐴 Лошадь спасла вас от смерти!\n"
            f"Награды не получены."
        )
    else:
        # Victory — give rewards based on waves defeated
        coin_reward = waves_defeated * user.level * 50
        xp_reward = waves_defeated * user.level * 30

        # Bonus from horse level and tier
        from database.crud import get_user as _get_user
        from database.engine import async_session as _sess
        async with _sess() as s:
            from database.models import Horse
            horse = await s.get(Horse, user_id)
            if horse:
                horse_mult = 1 + horse.level * 0.02 + horse.tier * 0.1
                coin_reward = int(coin_reward * horse_mult)
                xp_reward = int(xp_reward * horse_mult)

        await add_coins(user_id, coin_reward)
        await add_xp(user_id, xp_reward)

        result_msg = (
            f"⚔️ Эпический квест завершён!\n"
            f"Пройдено волн: {waves_defeated}/{chosen_waves}\n\n"
            f"💰 +{coin_reward:,} монет\n"
            f"⭐ +{xp_reward} XP"
        )

    # Clear epic quest state
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.epic_quest_wave = 0
            await s.commit()

    return {"success": True, "message": result_msg, "waves_defeated": waves_defeated}


async def _get_equipment_dict(user_id: int) -> dict:
    """Helper to get equipment dict."""
    from database.crud import get_equipment
    return await get_equipment(user_id)
