"""
Hunt commands: /hunt, /hunt hardmode, /hunt alone, /hunt together.
Fighting logic, mob drops, lootbox drops, death penalty.
"""
import random
import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.crud import get_user, get_equipment, get_inventory, update_cooldown, update_coolness, add_materials
from database.engine import async_session
from database.models import User, Horse, Marriage, Cooldown
from sqlalchemy import select
from game.player import calc_atk, calc_def, add_xp, add_coins, get_pet_bonuses, get_tt_bonus
from config import AREA_MOBS
from utils.keyboards import hunt_keyboard
import config
import json

router = Router()

# Mob drops per area (wiki: 4% chance, dark energy 0.1% from ALL mobs)
MOB_DROPS = {
    range(1, 3): "wolfskin",
    range(3, 5): "zombieeye",
    range(5, 7): "unicornhorn",
    range(7, 9): "mermaid_hair",
    range(9, 11): "chip",
    range(11, 16): "dragonscale",
}
BASE_DROP_CHANCE = 0.04  # 4% per hunt (2025 QOL buff)
DARK_ENERGY_CHANCE = 0.001  # 0.1% from ALL mobs

# Lootbox drop chances (GODLY is extremely rare)
LOOTBOX_DROPS = [
    (0.015, "common_lootbox"),
    (0.006, "uncommon_lootbox"),
    (0.002, "rare_lootbox"),
    (0.0008, "epic_lootbox"),
    (0.0003, "edgy_lootbox"),
    (0.00008, "omega_lootbox"),
    (0.00002, "godly_lootbox"),
]


def _calc_hp(level: int) -> int:
    return 100 + level * 5


def _get_mob_drop(area: int) -> str | None:
    """Get mob drop item for the given area."""
    for drop_range, item in MOB_DROPS.items():
        if area in drop_range:
            return item
    return None


def _roll_lootbox_drop(area: int, tt_count: int) -> str | None:
    """Roll for a lootbox drop. Higher area and TT = better chance."""
    tt_bonus = tt_count * 0.001
    for chance, box_type in LOOTBOX_DROPS:
        # Area 11+ gets bonus chance
        area_bonus = 0.002 if area >= 11 else 0
        if random.random() < chance + tt_bonus + area_bonus:
            return box_type
    return None


def _fight_round(player_atk: int, player_def: int, mob_hp: int, mob_atk: int, mob_def: int) -> tuple:
    """Run a single hunt combat round (5 rounds max). Returns (total_dmg_to_mob, total_dmg_to_player, won)."""
    total_dmg_to_mob = 0
    total_dmg_to_player = 0

    for _ in range(5):
        # Player attack
        raw = (player_atk - mob_def / 2) * random.uniform(0.9, 1.1)
        dmg = max(1, math.floor(raw))
        mob_hp -= dmg
        total_dmg_to_mob += dmg

        if mob_hp <= 0:
            return total_dmg_to_mob, total_dmg_to_player, True

        # Mob attack
        raw = (mob_atk - player_def / 2) * random.uniform(0.9, 1.1)
        dmg = max(1, math.floor(raw))
        total_dmg_to_player += dmg

    return total_dmg_to_mob, total_dmg_to_player, False


async def _get_horse_tier(user_id: int) -> int:
    """Get the player's horse tier."""
    async with async_session() as s:
        horse = await s.get(Horse, user_id)
        return horse.tier if horse else 0


async def _horse_save(user_id: int) -> bool:
    """Check if horse saves from death. Tier IV+ saves from death."""
    tier = await _get_horse_tier(user_id)
    return tier >= 4


async def _apply_death_penalty(user_id: int):
    """Apply death penalty: lose 1 level, lose XP gained this fight."""
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u and u.level > 1:
            u.level -= 1
            u.xp = 0
            await s.commit()


async def _handle_victory(user_id: int, area: int, tt_count: int, hardmode: bool) -> dict:
    """Process victory rewards: coins, XP, mob drops, lootbox."""
    tt_mult = 1 + get_tt_bonus(tt_count)
    pet_bonuses = await get_pet_bonuses(user_id)
    coin_mult = tt_mult + pet_bonuses.get("coins", 0)
    xp_mult = tt_mult + pet_bonuses.get("xp", 0)

    # Hardmode gives 3x rewards
    hm_mult = 3 if hardmode else 1

    coins = int(area * random.randint(10, 25) * coin_mult * hm_mult)
    xp = int(area * random.randint(15, 30) * xp_mult * hm_mult)

    await add_coins(user_id, coins)
    xp_result = await add_xp(user_id, xp)
    await update_coolness(user_id)

    drops = []

    # Mob drop — 4% base, scales with TT and horse tier
    drop_bonus = pet_bonuses.get("drop", 0.0)
    horse_tier = await _get_horse_tier(user_id)
    horse_drop_bonus = 0.01 if horse_tier >= 7 else 0  # Horse VII+ doubles drop chance
    tt_drop_bonus = tt_count * 0.002  # +0.2% per TT
    final_drop_chance = BASE_DROP_CHANCE + drop_bonus + horse_drop_bonus + tt_drop_bonus
    if hardmode:
        final_drop_chance *= 2

    mob_drop = _get_mob_drop(area)
    if mob_drop and random.random() < final_drop_chance:
        drops.append(mob_drop)
        await add_materials(user_id, mob_drop, 1)

    # Dark energy — 0.1% from ALL mobs, scales with TT
    de_chance = DARK_ENERGY_CHANCE + tt_count * 0.0002
    if random.random() < de_chance:
        drops.append("dark_energy")
        await add_materials(user_id, "dark_energy", 1)

    # Lootbox drop
    lootbox = _roll_lootbox_drop(area, tt_count)
    if lootbox:
        drops.append(lootbox)
        await add_materials(user_id, lootbox, 1)

    return {
        "coins": coins,
        "xp": xp,
        "drops": drops,
        "leveled_up": xp_result.get("leveled_up", False),
        "new_level": xp_result.get("new_level", 0),
    }


async def _handle_defeat(user_id: int, horse_save: bool, coins_lost: int) -> dict:
    """Process defeat: either horse saves (1 HP, no death) or death penalty."""
    if horse_save:
        # Horse saves: stay at 1 HP, no death penalty, but no rewards
        return {
            "horse_saved": True,
            "coins_lost": 0,
            "level_lost": False,
        }
    else:
        # Death: lose 1 level and all XP from this fight
        await _apply_death_penalty(user_id)
        return {
            "horse_saved": False,
            "coins_lost": coins_lost,
            "level_lost": True,
        }


async def _hunt_fight(user_id: int, hardmode: bool = False, alone: bool = False) -> dict:
    """Core hunt fight logic."""
    user = await get_user(user_id)
    eq = await get_equipment(user_id)
    if not user or not eq:
        return {"success": False, "message": "Игрок не найден."}

    weapon_tier = eq.get("weapon_tier", 1)
    armor_tier = eq.get("armor_tier", 1)
    player_atk = calc_atk(user.level, weapon_tier)
    player_def = calc_def(user.level, armor_tier)
    player_max_hp = _calc_hp(user.level)

    # Mob selection
    mob_pool = AREA_MOBS.get(user.area, AREA_MOBS.get(1))
    mob = dict(random.choice(mob_pool))

    if hardmode:
        # Hardmode: much stronger mobs (area 13+ only)
        mob["hp"] = math.floor(mob["hp"] * 2.5)
        mob["atk"] = math.floor(mob["atk"] * 2.5)
        mob["def"] = math.floor(mob["def"] * 2.5)
        mob["name"] = f"HARD {mob['name']}"
    elif alone:
        # Hunt alone: overpowered mob
        mob["hp"] = math.floor(mob["hp"] * 2.0)
        mob["atk"] = math.floor(mob["atk"] * 1.8)
        mob["def"] = math.floor(mob["def"] * 1.5)
        mob["name"] = f"SOLO {mob['name']}"
    else:
        # Normal hunt: mob scaled to player stats
        mob["atk"] = math.floor(player_atk * 0.8)
        mob["def"] = math.floor(player_def * 0.8)
        mob["hp"] = 30 + user.level * 15

    # Combat
    dmg_to_mob, dmg_to_player, won = _fight_round(player_atk, player_def, mob["hp"], mob["atk"], mob["def"])
    current_hp = max(0, player_max_hp - dmg_to_player)

    if won:
        rewards = await _handle_victory(user_id, user.area, user.tt_count, hardmode)
        return {
            "success": True, "victory": True, "mob": mob,
            "dmg_to_mob": dmg_to_mob, "dmg_to_player": dmg_to_player,
            "current_hp": current_hp, "max_hp": player_max_hp,
            **rewards,
        }
    else:
        # Defeat handling
        coins_lost = min(user.coins, user.coins // 10)
        horse_tier = await _get_horse_tier(user_id)
        horse_saves = horse_tier >= 4

        if horse_saves:
            # Horse saves: stay at 1 HP
            async with async_session() as s:
                u = await s.get(User, user_id)
                if u:
                    u.coins -= coins_lost
                    await s.commit()
            return {
                "success": True, "victory": False, "mob": mob,
                "dmg_to_mob": dmg_to_mob, "dmg_to_player": dmg_to_player,
                "current_hp": 1, "max_hp": player_max_hp,
                "horse_saved": True, "coins_lost": 0, "level_lost": False,
            }
        else:
            # Death: lose 1 level
            await _apply_death_penalty(user_id)
            async with async_session() as s:
                u = await s.get(User, user_id)
                if u:
                    u.coins -= coins_lost
                    await s.commit()
            return {
                "success": True, "victory": False, "mob": mob,
                "dmg_to_mob": dmg_to_mob, "dmg_to_player": dmg_to_player,
                "current_hp": 0, "max_hp": player_max_hp,
                "horse_saved": False, "coins_lost": coins_lost, "level_lost": True,
            }


@router.message(F.text == "/hunt")
@router.message(F.text.startswith("/hunt "))
async def cmd_hunt(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:]

    # Parse hunt variant
    hardmode = False
    alone = False
    together = False

    for arg in args:
        arg_lower = arg.lower()
        if arg_lower == "hardmode":
            hardmode = True
        elif arg_lower == "alone":
            alone = True
        elif arg_lower == "together":
            together = True

    # Area check for hardmode
    if hardmode and user.area < 13:
        await message.answer("❌ /hunt hardmode доступен с Area 13.")
        return

    # Level check for hunt alone
    if alone and user.level < 100:
        await message.answer("❌ /hunt alone доступен с уровня 100.")
        return

    # Hunt together: requires marriage
    if together:
        async with async_session() as s:
            result = await s.execute(
                select(Marriage).where(
                    (Marriage.user1_id == message.from_user.id) | (Marriage.user2_id == message.from_user.id)
                )
            )
            marriage = result.scalar_one_or_none()
            if not marriage:
                await message.answer("❌ /hunt together доступен только для женатых игроков.")
                return

            # Determine partner
            partner_id = marriage.user2_id if marriage.user1_id == message.from_user.id else marriage.user1_id

        # Hunt for self first
        allowed, remaining = await update_cooldown(message.from_user.id, "hunt")
        if not allowed:
            await message.answer(f"⏳ Кулдаун: {remaining}с")
            return

        result = await _hunt_fight(message.from_user.id, hardmode=hardmode, alone=alone)
        text = _format_hunt_result(message.from_user.first_name, result)

        # Hunt for partner
        allowed2, remaining2 = await update_cooldown(partner_id, "hunt")
        if allowed2:
            partner_result = await _hunt_fight(partner_id, hardmode=False, alone=False)
            partner_user = await get_user(partner_id)
            partner_name = partner_user.username if partner_user else "Партнёр"
            text += f"\n\n--- {partner_name} ---\n" + _format_hunt_result(partner_name, partner_result)
        else:
            text += f"\n\n--- Партнёр: кулдаун {remaining2}с ---"

        await message.answer(text, parse_mode="HTML", reply_markup=hunt_keyboard())
        return

    # Normal hunt
    allowed, remaining = await update_cooldown(message.from_user.id, "hunt")
    if not allowed:
        await message.answer(
            f"⏳ Кулдаун: {remaining}с",
            reply_markup=hunt_keyboard(is_on_cooldown=True, remaining=remaining)
        )
        return

    result = await _hunt_fight(message.from_user.id, hardmode=hardmode, alone=alone)
    text = _format_hunt_result(message.from_user.first_name, result)
    await message.answer(text, parse_mode="HTML", reply_markup=hunt_keyboard())


def _format_hunt_result(username: str, result: dict) -> str:
    """Format hunt result for display."""
    if not result["success"]:
        return result.get("message", "Ошибка")

    mob = result["mob"]

    if result["victory"]:
        text = (
            f"⚔️ <b>{username} охотится</b>\n\n"
            f"{mob['emoji']} {mob['name']}\n"
            f"Урон: {result['dmg_to_mob']} / {mob['hp']}\n\n"
            f"🏆 <b>Победа!</b>\n"
            f"💰 +{result['coins']:,} монет | ⭐ +{result['xp']:,} XP"
        )
        if result.get("leveled_up"):
            text += f"\n🎉 Уровень: {result['new_level']}!"
        if result.get("drops"):
            with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
                mat_names = json.load(f).get("names", {})
            drop_names = [mat_names.get(d, d.replace("_", " ").title()) for d in result["drops"]]
            text += f"\n🎁 Дроп: {', '.join(drop_names)}"
        if result.get("current_hp", 100) <= 0:
            text += f"\n\nHP: {result['current_hp']}/{result['max_hp']}"
    else:
        text = (
            f"⚔️ <b>{username} охотится</b>\n\n"
            f"{mob['emoji']} {mob['name']}\n"
            f"Урон: {result['dmg_to_mob']} / {mob['hp']}\n"
            f"Получено: {result['dmg_to_player']} урона\n\n"
        )
        if result.get("horse_saved"):
            text += f"🐴 <b>Лошадь спасла!</b> Вы на 1 HP. Без награды."
        else:
            text += f"💀 <b>Смерть!</b>"
            if result.get("level_lost"):
                text += f"\n📉 Потеряли 1 уровень."
            if result.get("coins_lost", 0) > 0:
                text += f"\n💸 Потеряно {result['coins_lost']:,} монет."
        text += f"\n\nHP: {result.get('current_hp', 0)}/{result['max_hp']}"

    return text


@router.callback_query(F.data == "action_hunt")
async def cb_hunt(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Сначала зарегистрируйтесь: /start", show_alert=True)
        return

    allowed, remaining = await update_cooldown(callback.from_user.id, "hunt")
    if not allowed:
        await callback.answer(f"Cooldown: {remaining}с", show_alert=True)
        return

    result = await _hunt_fight(callback.from_user.id)
    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    text = _format_hunt_result(callback.from_user.first_name, result)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=hunt_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=hunt_keyboard())
    await callback.answer()


@router.callback_query(F.data == "action_adventure")
async def cb_adventure(callback: CallbackQuery):
    from game.combat import fight_monster
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Сначала зарегистрируйтесь: /start", show_alert=True)
        return

    allowed, remaining = await update_cooldown(callback.from_user.id, "adventure")
    if not allowed:
        await callback.answer(f"Cooldown: {remaining}с", show_alert=True)
        return

    result = await fight_monster(callback.from_user.id, user.area, is_adventure=True)
    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    text = result.get("message", "")
    from utils.keyboards import adventure_keyboard
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=adventure_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=adventure_keyboard())
    await callback.answer()


@router.callback_query(F.data == "action_hunt_cd")
async def cb_hunt_cd(callback: CallbackQuery):
    await callback.answer("Cooldown!", show_alert=True)


@router.callback_query(F.data == "action_adventure_cd")
async def cb_adventure_cd(callback: CallbackQuery):
    await callback.answer("Cooldown!", show_alert=True)


@router.message(F.text == "/adventure")
async def cmd_adventure(message: Message):
    from game.combat import fight_monster
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь: /start")
        return

    allowed, remaining = await update_cooldown(message.from_user.id, "adventure")
    if not allowed:
        await message.answer(
            f"⏳ Кулдаун: {remaining}с",
        )
        return

    result = await fight_monster(message.from_user.id, user.area, is_adventure=True)
    text = result.get("message", "Ошибка")
    await message.answer(text, parse_mode="HTML")
