import random
import math
import json
import config
from game.player import calc_atk, calc_def, add_xp, add_coins, get_pet_bonuses, get_tt_bonus, get_tt_drop_bonus, get_tt_items_bonus
from database.crud import get_user, get_equipment, get_inventory


def calc_damage(atk: int, defender_def: int) -> int:
    """Damage = max(1, floor((ATK - DEF/2) * random(0.9, 1.1)))"""
    raw = (atk - defender_def / 2) * random.uniform(0.9, 1.1)
    return max(1, math.floor(raw))


def get_area_base_stats(area: int) -> dict:
    """Get base stats for an area's mobs (used in /adventure)."""
    import json as _json
    from pathlib import Path
    with open(config.DATA_DIR / "areas.json", "r", encoding="utf-8") as f:
        areas = _json.load(f).get("areas", {})
    a = areas.get(str(area), {})
    return {
        "hp": a.get("base_hp", 100),
        "atk": a.get("base_atk", 10),
        "def": a.get("base_def", 5),
    }


async def fight_monster(user_id: int, area_num: int, is_adventure: bool = False, hardmode: bool = False) -> dict:
    """Run full fight. Returns result dict with messages and rewards.

    Wiki mechanics:
    - HP persists between fights (stored in DB current_hp)
    - If current_hp == 0, init to max HP on first fight
    - On death without tier IV horse: lose 1 level
    - On death with tier IV+ horse: horse saves you, stay at 1 HP, no rewards
    - Damage reduced by ATK/DEF stats (1 point = 1 less damage taken)
    """
    from database.engine import async_session
    from database.models import User, Horse

    user = await get_user(user_id)
    eq = await get_equipment(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    weapon_tier = eq.get("weapon_tier", 1)
    armor_tier = eq.get("armor_tier", 1)
    weapon_enchant = eq.get("sword_enchant", {}).get("bonus_pct", 0)
    armor_enchant = eq.get("armor_enchant", {}).get("bonus_pct", 0)

    player_atk = calc_atk(user.level, weapon_tier, weapon_enchant)
    player_def = calc_def(user.level, armor_tier, armor_enchant)
    max_hp = 100 + user.level * 5

    # Wiki: damage taken is reduced by ATK and DEF stats (1 point = 1 less damage)

    # Init HP if needed (first fight after TT or registration)
    if user.current_hp <= 0:
        async with async_session() as s:
            u = await s.get(User, user_id)
            if u:
                u.current_hp = max_hp
                await s.commit()
        player_hp = max_hp
    else:
        player_hp = user.current_hp

    # Hardmode multiplier
    hm_mult = 2.5 if hardmode else 1.0

    if is_adventure:
        base = get_area_base_stats(area_num)
        mob_atk = math.floor(base["atk"] * 1.3 * hm_mult)
        mob_def = math.floor(base["def"] * 1.3 * hm_mult)
        mob_hp = math.floor(base["hp"] * 1.3 * hm_mult)
    else:
        mob_atk = math.floor(player_atk * 0.8 * hm_mult)
        mob_def = math.floor(player_def * 0.8 * hm_mult)
        mob_hp = int((30 + user.level * 15) * hm_mult)

    log = []

    # --- Combat rounds ---
    for round_num in range(1, 6):
        dmg_to_mob = calc_damage(player_atk, mob_def)
        mob_hp -= dmg_to_mob
        log.append(f"Раунд {round_num}: Вы наносите {dmg_to_mob} урона.")

        if mob_hp <= 0:
            break

        dmg_to_player = calc_damage(mob_atk, player_def)
        player_hp -= dmg_to_player
        log.append(f"Раунд {round_num}: Враг наносит вам {dmg_to_player} урона.")

        if player_hp <= 0:
            break

    # --- Save HP to DB ---
    new_hp = max(0, player_hp)
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.current_hp = new_hp
            await s.commit()

    if mob_hp <= 0:
        # Victory
        tt_mult = 1 + get_tt_bonus(user.tt_count)
        pet_bonuses = await get_pet_bonuses(user_id)
        coin_mult = tt_mult + pet_bonuses.get("coins", 0)
        xp_mult = tt_mult + pet_bonuses.get("xp", 0)

        coins = int(area_num * random.randint(10, 25) * coin_mult)
        xp = int(area_num * random.randint(15, 30) * xp_mult)

        # Drop check — per-mob drop from AREA_MOBS
        drops = []
        drop_bonus = pet_bonuses.get("drop", 0.0)
        tt_drop_mult = 1 + get_tt_drop_bonus(user.tt_count)  # wiki: % extra chance
        from config import AREA_MOBS
        mob_pool = AREA_MOBS.get(area_num, AREA_MOBS.get(1))
        mob_choice = random.choice(mob_pool)
        mob_drop = mob_choice.get("drop")
        drop_mult = 1.0
        from database.crud import has_active_returning_event
        if await has_active_returning_event(user_id):
            drop_mult = config.RETURNING_DROP_MULTIPLIER
        if mob_drop and random.random() < mob_drop["chance"] * tt_drop_mult * (1 + drop_bonus) * drop_mult:
            drops.append(mob_drop["item"])

        await add_coins(user_id, coins)
        xp_result = await add_xp(user_id, xp)

        msg = "\n".join(log)
        msg += f"\n\n🏆 Победа!"
        msg += f"\n💰 +{coins} монет"
        msg += f"\n⭐ +{xp} XP"
        if drops:
            with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as _f:
                _mat_data = json.load(_f)
            mat_names = _mat_data.get("names", {})
            drop_names = [mat_names.get(d, d) for d in drops]
            msg += f"\n🎁 Дроп: {', '.join(drop_names)}"
        if xp_result["leveled_up"]:
            msg += f"\n🎉 Уровень повышен! Level {xp_result['new_level']}!"

        # Monster drops: rare lootbox chance (scales with area)
        lootbox_chance = min(0.01 + area_num * 0.002, 0.05)
        if await has_active_returning_event(user_id):
            lootbox_chance *= config.RETURNING_DROP_MULTIPLIER
        if random.random() < lootbox_chance:
            lootbox_types = ["common_lootbox", "uncommon_lootbox", "rare_lootbox"]
            lootbox = random.choice(lootbox_types)
            from database.crud import add_materials
            await add_materials(user_id, lootbox, 1)
            msg += f"\n📦 {lootbox.replace('_', ' ')}!"

        # Smol coin drops during Returning Event
        if await has_active_returning_event(user_id):
            smol_lo, smol_hi = config.RETURNING_SMOL_PER_ACTION
            smol = random.randint(smol_lo, smol_hi)
            await add_materials(user_id, "smol_coin", smol)
            from game.returning import track_smol_coins
            await track_smol_coins(user_id, smol)
            msg += f"\n🪙 +{smol} smol coins"

        # Quest hook
        from game.quest import on_hunt_kill, on_adventure_kill
        if is_adventure:
            await on_adventure_kill(user_id, "ADVENTURE_MOB")
        else:
            await on_hunt_kill(user_id, "HUNT_MOB")

        return {"success": True, "victory": True, "message": msg, "coins": coins, "xp": xp, "drops": drops}
    else:
        # Defeat — Wiki death mechanics
        async with async_session() as s:
            u = await s.get(User, user_id)
            horse = await s.get(Horse, user_id)
            horse_tier = horse.tier if horse else 0

            if horse_tier >= 4:
                # Wiki: tier IV+ horse saves you — stay at 1 HP, no rewards
                if u:
                    u.current_hp = 1
                msg = "\n".join(log)
                msg += f"\n\n🐴 Лошадь спасла вас от смерти!"
                msg += f"\nHP: 1 / {max_hp}"
                msg += f"\n⚠️ Выживете, но награды не получены."
                await s.commit()
                return {"success": True, "victory": False, "message": msg, "horse_save": True}
            else:
                # Wiki: no horse — lose 1 level, reset HP to max
                if u:
                    if u.level > 1:
                        u.level -= 1
                    u.current_hp = max_hp  # Reset to full after death
                    u.coins = max(0, u.coins - (u.coins // 10))  # Lose 10% coins
                msg = "\n".join(log)
                msg += f"\n\n💀 Вы погибли!"
                msg += f"\n📉 Потеряно: 1 уровень (уровень {user.level - 1})"
                coins_lost = user.coins // 10
                if coins_lost > 0:
                    msg += f"\n💰 Потеряно: {coins_lost} монет"
                msg += f"\n❤️ HP восстановлено: {max_hp}/{max_hp}"
                msg += f"\n\n💡 Используйте /heal перед охотой!"
                await s.commit()

        return {"success": True, "victory": False, "message": msg, "coins_lost": coins_lost}
        if coins_lost > 0:
            msg += f"\n💸 Потеряно {coins_lost} монет."

        return {"success": True, "victory": False, "message": msg, "coins_lost": coins_lost}


def calc_dungeon_boss_coop(base_hp: int, base_atk: int, player_count: int) -> dict:
    """Dungeon boss scaling for cooperative play."""
    hp = math.floor(base_hp * player_count ** 0.7)
    atk = math.floor(base_atk * (1 + 0.15 * (player_count - 1)))
    return {"hp": hp, "atk": atk}
