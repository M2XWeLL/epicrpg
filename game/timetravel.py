"""
Time Travel system — wiki-accurate reset mechanics.

What gets RESET:
  - Level (back to 1), XP, area (back to 1)
  - Equipment (weapon/armor back to tier 1)
  - All materials / inventory (except dragonessence, timedragonessence, arenacookie)
  - Cooldowns
  - Cook stat boosts (permanent until TT)
  - Cook multipliers (permanent until TT)

What is KEPT:
  - Coins (incl. bank) — wiki: "Coins - bank included; refers to epic and guild coins as well"
  - Epic Coins
  - Horse (tier stays the same)
  - Arena Cookies
  - Professions (levels + tools)
  - Pets
  - Dragon essences (not Dragon scales!)
  - Time Dragon Essences
  - Event items (if active)
  - Epic Shop purchases

TT Bonuses (quadratic formulas):
  XP:       (99 + x) * x / 2
  Duel XP:  (99 + x) * x / 4
  Drops:    (49 + x) * x / 2
  Items:    (49 + x) * x / 2

TT also increases horse breeding chance (already in breeding code via tt_count).

Titles:
  TT1:  "Time traveler"
  TT2:  "One time wasn't enough"
  TT5:  "I spend too much time here"
  TT10: "OOF"
  TT25: "OOFMEGA"
  TT50: "GOOFDLY"
  TT75: "VOOFID"

Coin Trading restrictions:
  After TT2: cannot give/receive coins from TT0-TT1 players
  After TT20: cannot give/receive coins from TT0-TT19 players

Super Time Travel (STT):
  Unlocked after defeating Dungeon 15 and obtaining TIME KEY.
  Player sacrifices inventory for STT Score, then picks a reward.
"""
import config
from game.player import get_tt_xp_bonus, get_tt_drop_bonus, get_tt_items_bonus


def get_tt_table_row(tt_count: int) -> dict:
    """Get a single row of the TT bonus table for display (as percentages)."""
    return {
        "exp": (99 + tt_count) * tt_count / 2,
        "duel_exp": (99 + tt_count) * tt_count / 4,
        "drops": (49 + tt_count) * tt_count / 2,
        "items": (49 + tt_count) * tt_count / 2,
    }


def get_max_dungeon(tt_count: int) -> int:
    """Highest dungeon unlocked by TT count (wiki table)."""
    return config.TT_DUNGEON_UNLOCK.get(tt_count, 15 if tt_count >= 25 else 14)


def can_trade_coins(sender_tt: int, receiver_tt: int) -> bool:
    """Check if coin trading is allowed between two players (wiki rules)."""
    # After TT2: can't trade with TT0-TT1
    if sender_tt >= 2 and receiver_tt <= 1:
        return False
    # After TT20: can't trade with TT0-TT19
    if sender_tt >= 20 and receiver_tt <= 19:
        return False
    return True


def get_tt_title(tt_count: int) -> str | None:
    """Get the highest title unlocked by TT count."""
    best = None
    for threshold, title in sorted(config.TT_TITLES.items()):
        if tt_count >= threshold:
            best = title
    return best


async def can_timetravel(user_id: int) -> dict:
    from database.crud import get_user
    user = await get_user(user_id)
    if not user:
        return {"can": False, "message": "Игрок не найден."}

    required_level = config.BASE_MAX_LEVEL + user.tt_count * config.TT_LEVEL_BONUS

    if user.area < 11:
        return {
            "can": False,
            "message": f"❌ Нужна Area 11+ для Time Travel. Сейчас: Area {user.area}."
        }

    if user.level < required_level:
        return {
            "can": False,
            "message": f"❌ Нужен уровень {required_level} для Time Travel (сейчас: {user.level})."
        }

    return {"can": True, "required_level": required_level, "current_tt": user.tt_count}


async def do_timetravel(user_id: int) -> dict:
    """Execute a Time Travel — reset progress, keep specified items, apply bonuses."""
    result = await can_timetravel(user_id)
    if not result["can"]:
        return {"success": False, **result}

    from database.engine import async_session
    from database.models import User, Inventory, Cooldown
    from database.crud import get_inventory
    import json

    async with async_session() as s:
        user = await s.get(User, user_id)
        inv = await s.get(Inventory, user_id)
        cd = await s.get(Cooldown, user_id)
        if not user:
            return {"success": False, "message": "Игрок не найден."}

        user.tt_count += 1

        # RESET: level, xp, area
        user.level = 1
        user.xp = 0
        user.area = 1
        user.max_area = max(user.max_area, 1)  # keep max_area

        # KEEP: coins, epic_coins, bank — wiki says all stay
        # (coins, epic_coins, bank are NOT reset)

        # RESET: equipment (back to tier 1)
        if inv:
            inv.equipment = '{"weapon_tier": 1, "armor_tier": 1}'
            # RESET: materials (except what we keep)
            old_mats = json.loads(inv.materials) if inv.materials else {}

            # Keep: dragonessence, timedragonessence, arenacookie
            # Keep: items bought from Epic Shop (magic_bed, etc.)
            # Keep: event items (smol_coin if event active)
            keep_mats = {}
            for keep_key in ["dragonessence", "timedragonessence", "arenacookie"]:
                if old_mats.get(keep_key, 0) > 0:
                    keep_mats[keep_key] = old_mats[keep_key]

            from config import DEFAULT_MATERIALS
            new_mats = {k: 0 for k in DEFAULT_MATERIALS}
            new_mats.update(keep_mats)
            inv.materials = json.dumps(new_mats)

        # RESET: cook boosts (permanent until TT per wiki)
        user.cook_hp_boost = 0
        user.cook_atk_boost = 0
        user.cook_def_boost = 0
        user.cook_level_boost = 0
        user.cook_coins_mult = 0
        user.cook_fish_mult = 0
        user.cook_logs_mult = 0
        user.cook_flat_coins = 0

        # RESET: cooldowns
        if cd:
            from datetime import datetime
            cd.hunt_last = datetime.min
            cd.adventure_last = datetime.min
            cd.chop_last = datetime.min
            cd.mine_last = datetime.min
            cd.fish_last = datetime.min
            cd.guild_raid_last = datetime.min
            cd.last_daily = datetime.min
            cd.last_weekly = datetime.min
            cd.last_vote = datetime.min
            cd.last_arena = datetime.min
            cd.last_duel = datetime.min
            cd.last_training = datetime.min
            cd.last_farm = datetime.min

        # KEEP: horse (tier stays), pets, professions (tools), epic_coins, bank, title, coolness

        # Apply TT title
        title = get_tt_title(user.tt_count)
        if title:
            user.title = title

        await s.commit()

    tt_count = user.tt_count
    row = get_tt_table_row(tt_count)
    enchant_mult = 1 + tt_count * config.TT_ENCHANT_BONUS_PER_TT
    cd_reduction = min(tt_count * config.TT_CD_REDUCTION, config.TT_CD_MAX) * 100

    # Get max dungeon for new TT count
    max_dung = get_max_dungeon(tt_count)

    msg = (
        f"⏳ <b>Time Travel #{tt_count}!</b>\n\n"
        f"📊 Прогресс сброшен:\n"
        f"  • Уровень: 1\n"
        f"  • Локация: Area 1\n"
        f"  • Снаряжение: Тир 1\n"
        f"  • Материалы: очищены\n\n"
        f"🎁 Постоянные бонусы:\n"
        f"  • +{row['exp']:.0f}% к XP\n"
        f"  • +{row['duel_exp']:.0f}% к XP в дуэлях\n"
        f"  • +{row['drops']:.0f}% к шансу дропа мобов\n"
        f"  • +{row['items']:.0f}% к предметам в командах работы\n"
        f"  • x{enchant_mult:.1f} множитель зачарования\n"
        f"  • -{cd_reduction:.0f}% к кулдаунам\n\n"
        f"🏰 Макс. данжон: D{max_dung}\n"
    )

    if title:
        msg += f"\n🏆 Титул: <b>{title}</b>\n"

    msg += (
        f"\n🔒 Сохранено:\n"
        f"  Монеты, банк, EPIC монеты, лошадь, питомцы, "
        f"профессии, печенье арены, эссенции"
    )

    return {
        "success": True,
        "message": msg,
        "tt_count": tt_count,
    }


# --- Super Time Travel (STT) ---

# STT Score values per item (wiki)
STT_SCORE_TABLE = {
    "level": 1,  # from stats + level itself
    "ruby": 1,
    "ultra_omega_gear": 155.5,  # per piece, but real score ~355.5 since forged at 200+
    "dragon_scale": 0.5,  # 2 per 1 score
    "chip": 0.25,  # 4 per 1 score
    "mermaid_hair": 1,
    "unicornhorn": 1,
    "zombieeye": 1,
    "wolfskin": 1,
    "common_lootbox": 0.05,
    "uncommon_lootbox": 0.1,
    "rare_lootbox": 0.15,
    "epic_lootbox": 0.2,
    "edgy_lootbox": 0.25,
    "omega_lootbox": 2.5,
    "godly_lootbox": 25,
    "watermelon": 1,  # 12 per 1
    "bread": 1,  # 25 per 1
    "carrot": 1,  # 30 per 1
    "potato": 1,  # 35 per 1
    "seed": 1,  # 2500 per 1
    "lotteryticket": 100,  # 20 per 1
}

# Items that contribute to STT score — value = items needed per 1 score point (wiki table)
STT_CONTRIBUTE_ITEMS = {
    "ruby": 25, "chip": 4, "mermaid_hair": 1, "unicornhorn": 7,
    "zombieeye": 10, "wolfskin": 20,
    "common_lootbox": 20, "uncommon_lootbox": 10, "rare_lootbox": 7,
    "epic_lootbox": 5, "edgy_lootbox": 4,
    "omega_lootbox": 0.4, "godly_lootbox": 0.04,
    "Watermelon": 12, "bread": 25, "carrot": 30, "potato": 35,
    "seed": 2500, "lotteryticket": 20,
    "dragonscale": 2,
}

# STT Rewards (wiki)
STT_REWARDS = {
    "life":       {"name": "+25 HP",                "cost": 50},
    "at":         {"name": "+50 ATK",               "cost": 400},
    "def":        {"name": "+50 DEF",               "cost": 400},
    "area_2":     {"name": "Start in Area 2",       "cost": 2000},
    "area_3":     {"name": "Start in Area 3",       "cost": 4500},
    "ultra_logs": {"name": "10 Ultra Logs",         "cost": 1750},
    "drops":      {"name": "35 of each Mob Drop",   "cost": 400},
    "omega_lootbox": {"name": "OMEGA Lootbox",      "cost": 500},
    "godly_lootbox": {"name": "GODLY Lootbox",      "cost": 6500},
    "pet_i":      {"name": "Tier I Pet",            "cost": 300},
    "pet_iii":    {"name": "Tier III Pet",           "cost": 1500},
    "skilled_pet": {"name": "Tier I Pet + 1 skill", "cost": 4500},
}


def calc_stt_score(user, inv: dict) -> float:
    """Calculate Super Time Travel score from player stats and inventory."""
    score = 0.0

    # Level score (from stats + level itself)
    # Wiki: "0.5 score from levels itself + 1 ATK + 1 DEF + 5 HP = 0.4 score"
    # Simplified: level itself gives some score
    from game.player import calc_atk, calc_def
    max_hp = 100 + user.level * 5
    atk = calc_atk(user.level, 1)  # base ATK
    def_ = calc_def(user.level, 1)  # base DEF
    # Wiki formula: level_score = level * 0.5 (levels) + atk * 0.1 + def_ * 0.1 + max_hp * 0.01
    # But simplified to: score = level (per wiki "Level* 1")
    score += user.level

    # Equipment score (Ultra-Omega gear = 155.5 per piece, but since forged at 200+ real = 355.5)
    eq_raw = inv.get("equipment", "{}")
    import json as _json
    try:
        eq = _json.loads(eq_raw) if isinstance(eq_raw, str) else eq_raw
    except Exception:
        eq = {}
    weapon_tier = eq.get("weapon_tier", 1)
    armor_tier = eq.get("armor_tier", 1)
    if weapon_tier >= 200:  # ULTRA-OMEGA
        score += 355.5
    if armor_tier >= 200:
        score += 355.5

    # Material scores (per_item = items needed for 1 score point)
    for item_id, items_per_point in STT_CONTRIBUTE_ITEMS.items():
        amt = inv.get(item_id, 0)
        if amt > 0 and items_per_point > 0:
            score += amt / items_per_point

    return round(score, 1)


async def can_super_timetravel(user_id: int) -> dict:
    """Check if player can do Super Time Travel."""
    from database.crud import get_user
    user = await get_user(user_id)
    if not user:
        return {"can": False, "message": "Игрок не найден."}

    # Wiki: requires defeating D15 and obtaining TIME KEY
    # For now, require TT25+ (post-game)
    if user.tt_count < 25:
        return {
            "can": False,
            "message": f"❌ Super Time Travel доступен после TT25. У вас: TT{user.tt_count}."
        }

    # Check if player has TIME KEY from D15
    inv = await get_inventory(user_id)
    # TODO: check for time_key when D15 is fully implemented

    return {"can": True, "tt_count": user.tt_count}


async def do_super_timetravel(user_id: int, reward_id: str) -> dict:
    """Execute Super Time Travel: sacrifice items for score, give chosen reward."""
    check = await can_super_timetravel(user_id)
    if not check["can"]:
        return {"success": False, **check}

    reward = STT_REWARDS.get(reward_id)
    if not reward:
        return {"success": False, "message": f"❌ Неизвестная награда: {reward_id}"}

    from database.engine import async_session
    from database.models import User, Inventory, Cooldown
    from database.crud import get_inventory, get_user
    import json

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    inv_data = await get_inventory(user_id)
    score = calc_stt_score(user, inv_data)

    if score < reward["cost"]:
        return {
            "success": False,
            "message": f"❌ Недостаточно очков STT. Нужно: {reward['cost']}, у вас: {score}"
        }

    # Execute STT
    async with async_session() as s:
        user = await s.get(User, user_id)
        inv = await s.get(Inventory, user_id)
        cd = await s.get(Cooldown, user_id)
        if not user:
            return {"success": False, "message": "Игрок не найден."}

        user.tt_count += 1

        # RESET level, xp, area (same as regular TT)
        user.level = 1
        user.xp = 0
        user.area = 1

        # KEEP coins, epic_coins, bank (same as regular TT)

        # RESET equipment and materials
        if inv:
            inv.equipment = '{"weapon_tier": 1, "armor_tier": 1}'
            old_mats = json.loads(inv.materials) if inv.materials else {}
            keep_mats = {}
            for keep_key in ["dragonessence", "timedragonessence", "arenacookie"]:
                if old_mats.get(keep_key, 0) > 0:
                    keep_mats[keep_key] = old_mats[keep_key]
            from config import DEFAULT_MATERIALS
            new_mats = {k: 0 for k in DEFAULT_MATERIALS}
            new_mats.update(keep_mats)
            inv.materials = json.dumps(new_mats)

        # RESET cook boosts
        user.cook_hp_boost = 0
        user.cook_atk_boost = 0
        user.cook_def_boost = 0
        user.cook_level_boost = 0
        user.cook_coins_mult = 0
        user.cook_fish_mult = 0
        user.cook_logs_mult = 0
        user.cook_flat_coins = 0

        # RESET cooldowns
        if cd:
            from datetime import datetime
            cd.hunt_last = datetime.min
            cd.adventure_last = datetime.min
            cd.chop_last = datetime.min
            cd.mine_last = datetime.min
            cd.fish_last = datetime.min
            cd.guild_raid_last = datetime.min
            cd.last_daily = datetime.min
            cd.last_weekly = datetime.min
            cd.last_vote = datetime.min
            cd.last_arena = datetime.min
            cd.last_duel = datetime.min
            cd.last_training = datetime.min
            cd.last_farm = datetime.min

        # Apply STT reward
        if reward_id == "life":
            user.cook_hp_boost = 25
        elif reward_id == "at":
            user.cook_atk_boost = 50
        elif reward_id == "def":
            user.cook_def_boost = 50
        elif reward_id == "area_2":
            user.area = 2
            user.max_area = max(user.max_area, 2)
        elif reward_id == "area_3":
            user.area = 3
            user.max_area = max(user.max_area, 3)
        elif reward_id == "ultra_logs":
            if inv:
                old_mats = json.loads(inv.materials) if inv.materials else {}
                old_mats["ultra_log"] = old_mats.get("ultra_log", 0) + 10
                inv.materials = json.dumps(old_mats)
        elif reward_id == "drops":
            if inv:
                old_mats = json.loads(inv.materials) if inv.materials else {}
                mob_drops = ["wolfskin", "zombieeye", "unicornhorn", "mermaid_hair", "ruby", "chip", "dragonscale"]
                for d in mob_drops:
                    old_mats[d] = old_mats.get(d, 0) + 35
                inv.materials = json.dumps(old_mats)
        elif reward_id == "omega_lootbox":
            if inv:
                old_mats = json.loads(inv.materials) if inv.materials else {}
                old_mats["omega_lootbox"] = old_mats.get("omega_lootbox", 0) + 1
                inv.materials = json.dumps(old_mats)
        elif reward_id == "godly_lootbox":
            if inv:
                old_mats = json.loads(inv.materials) if inv.materials else {}
                old_mats["godly_lootbox"] = old_mats.get("godly_lootbox", 0) + 1
                inv.materials = json.dumps(old_mats)

        # Apply TT title
        title = get_tt_title(user.tt_count)
        if title:
            user.title = title

        await s.commit()

    tt_count = user.tt_count
    row = get_tt_table_row(tt_count)

    return {
        "success": True,
        "message": (
            f"⏳ <b>Super Time Travel #{tt_count}!</b>\n\n"
            f"📊 STT Score: {score}\n"
            f"🎁 Награда: {reward['name']}\n\n"
            f"🎁 Бонусы:\n"
            f"  • +{row['exp']:.0f}% к XP\n"
            f"  • +{row['drops']:.0f}% к дропу\n"
            f"  • +{row['items']:.0f}% к предметам\n\n"
            f"🔒 Сохранено: монеты, банк, EPIC монеты, лошадь, питомцы"
        ),
        "tt_count": tt_count,
    }
