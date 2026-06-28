"""
Arena, duel, and miniboss fighting logic.
"""
import random
import math
import config
from game.player import calc_atk, calc_def, get_tt_bonus, get_pet_bonuses, add_xp, add_coins


async def duel_fight(challenger_id: int, target_id: int) -> dict:
    from database.crud import get_user, get_equipment

    c_user = await get_user(challenger_id)
    t_user = await get_user(target_id)
    if not c_user or not t_user:
        return {"success": False, "message": "Один из игроков не найден."}

    c_eq = await get_equipment(challenger_id)
    t_eq = await get_equipment(target_id)

    c_atk = calc_atk(c_user.level, c_eq.get("weapon_tier", 1), c_eq.get("sword_enchant", {}).get("bonus_pct", 0))
    c_def = calc_def(c_user.level, c_eq.get("armor_tier", 1), c_eq.get("armor_enchant", {}).get("bonus_pct", 0))
    t_atk = calc_atk(t_user.level, t_eq.get("weapon_tier", 1), t_eq.get("sword_enchant", {}).get("bonus_pct", 0))
    t_def = calc_def(t_user.level, t_eq.get("armor_tier", 1), t_eq.get("armor_enchant", {}).get("bonus_pct", 0))

    c_hp = 100 + c_user.level * 5
    t_hp = 100 + t_user.level * 5

    log = []
    for rnd in range(1, 11):
        dmg = max(1, math.floor((c_atk - t_def / 2) * random.uniform(0.9, 1.1)))
        t_hp -= dmg
        log.append(f"Раунд {rnd}: {c_user.username} наносит {dmg} урона.")
        if t_hp <= 0:
            break

        dmg2 = max(1, math.floor((t_atk - c_def / 2) * random.uniform(0.9, 1.1)))
        c_hp -= dmg2
        log.append(f"Раунд {rnd}: {t_user.username} наносит {dmg2} урона.")
        if c_hp <= 0:
            break

    if t_hp <= 0:
        coins = min(c_user.coins, 500 + c_user.level * 10)
        await add_coins(challenger_id, coins)
        return {
            "success": True, "victory": True, "winner": c_user.username,
            "loser": t_user.username, "coins": coins,
            "log": "\n".join(log),
        }
    else:
        coins = min(t_user.coins, 500 + t_user.level * 10)
        await add_coins(target_id, coins)
        return {
            "success": True, "victory": False, "winner": t_user.username,
            "loser": c_user.username, "coins": coins,
            "log": "\n".join(log),
        }


async def arena_fight(user_id: int) -> dict:
    from database.crud import get_user, get_equipment

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    eq = await get_equipment(user_id)
    player_atk = calc_atk(user.level, eq.get("weapon_tier", 1))
    player_def = calc_def(user.level, eq.get("armor_tier", 1))
    player_hp = 100 + user.level * 5

    # Generate arena opponent (scaled to player)
    opponent_names = ["GLADIATOR", "FIGHTER", "WARRIOR", "BERSERKER", "CHAMPION"]
    opponent_emoji = ["⚔️", "🗡️", "🛡️", "⚡", "🔥"]
    idx = random.randint(0, len(opponent_names) - 1)

    opp_level = max(1, user.level + random.randint(-3, 5))
    opp_atk = calc_atk(opp_level, random.randint(max(1, eq.get("weapon_tier", 1) - 1), eq.get("weapon_tier", 1) + 1))
    opp_def = calc_def(opp_level, random.randint(max(1, eq.get("armor_tier", 1) - 1), eq.get("armor_tier", 1) + 1))
    opp_hp = 100 + opp_level * 5

    log = [f"⚔️ Арена: {user.username} vs {opponent_emoji[idx]} {opponent_names[idx]} (Lvl {opp_level})"]

    for rnd in range(1, 11):
        dmg = max(1, math.floor((player_atk - opp_def / 2) * random.uniform(0.9, 1.1)))
        opp_hp -= dmg
        log.append(f"Раунд {rnd}: Вы наносите {dmg} урона.")
        if opp_hp <= 0:
            break

        dmg2 = max(1, math.floor((opp_atk - player_def / 2) * random.uniform(0.9, 1.1)))
        player_hp -= dmg2
        log.append(f"Раунд {rnd}: Противник наносит {dmg2} урона.")
        if player_hp <= 0:
            break

    if opp_hp <= 0:
        reward = config.ARENA_REWARD_BASE + user.level * 20
        xp = user.level * 15
        await add_coins(user_id, reward)
        await add_xp(user_id, xp)
        return {
            "success": True, "victory": True, "log": "\n".join(log),
            "coins": reward, "xp": xp,
        }
    else:
        return {
            "success": True, "victory": False, "log": "\n".join(log),
            "coins": 0, "xp": 0,
        }


async def miniboss_fight(user_id: int) -> dict:
    from database.crud import get_user, get_equipment
    from game.combat import calc_damage

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    eq = await get_equipment(user_id)
    player_atk = calc_atk(user.level, eq.get("weapon_tier", 1))
    player_def = calc_def(user.level, eq.get("armor_tier", 1))
    player_hp = 100 + user.level * 5

    # Mini-boss stats
    boss_hp = user.level * 80
    boss_atk = user.level * 12
    boss_def = user.level * 5

    log = [f"👹 MINI BOSS (HP: {boss_hp}, ATK: {boss_atk}, DEF: {boss_def})"]

    for rnd in range(1, 16):
        dmg = calc_damage(player_atk, boss_def)
        boss_hp -= dmg
        log.append(f"Раунд {rnd}: Вы наносите {dmg} урона.")
        if boss_hp <= 0:
            break

        dmg2 = calc_damage(boss_atk, player_def)
        player_hp -= dmg2
        log.append(f"Раунд {rnd}: Босс наносит {dmg2} урона.")
        if player_hp <= 0:
            break

    if boss_hp <= 0:
        reward = user.level * 100
        xp = user.level * 60
        await add_coins(user_id, reward)
        await add_xp(user_id, xp)
        return {
            "success": True, "victory": True, "log": "\n".join(log),
            "coins": reward, "xp": xp,
        }
    else:
        return {
            "success": True, "victory": False, "log": "\n".join(log),
            "coins": 0, "xp": 0,
        }