"""
Dungeon commands: /dungeon, /dungeon [number], /dungeon buy [number],
/dungeon fight, /dungeon info, /dungeon invite @user, /dungeon accept
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, get_equipment, get_inventory
from database.engine import async_session
from database.models import Pet, Horse
from sqlalchemy import select
from game.dungeons import (
    get_dungeon, get_dungeon_commands, buy_dungeon_key,
    fight_standard_dungeon, create_dungeon_invite, accept_dungeon_invite,
    fight_d15, fight_d10,
)
from game.player import calc_atk, calc_def
import config

router = Router()


@router.message(F.text == "/dungeon")
@router.message(F.text.startswith("/dungeon "))
async def cmd_dungeon(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    # /dungeon — show available dungeons
    if not args:
        await _show_dungeon_list(message, user)
        return

    subcmd = args[0].lower()

    # /dungeon buy [number]
    if subcmd == "buy":
        if len(args) < 2:
            await message.answer("Формат: /dungeon buy [номер]\nПример: /dungeon buy 1")
            return
        try:
            dnum = int(args[1])
        except ValueError:
            await message.answer("❌ Введите номер данжона (1-9).")
            return
        result = await buy_dungeon_key(message.from_user.id, dnum)
        await message.answer(result["message"], parse_mode="HTML")
        return

    # /dungeon info [number]
    if subcmd == "info":
        if len(args) >= 2:
            try:
                dnum = int(args[1])
                await _show_dungeon_info_detail(message, user, dnum)
            except ValueError:
                await _show_dungeon_info(message, user)
        else:
            await _show_dungeon_info(message, user)
        return

    # /dungeon fight — fight dungeon for current area
    if subcmd == "fight":
        dungeon_num = user.area - 1
        if dungeon_num < 1 or dungeon_num > 15:
            await message.answer("❌ Нет данжона для вашей локации.")
            return
        if dungeon_num == 15:
            result = await fight_d15(message.from_user.id)
            await message.answer(result["message"], parse_mode="HTML")
        elif 1 <= dungeon_num <= 9:
            result = await fight_standard_dungeon(message.from_user.id, dungeon_num)
            await _handle_fight_result(message, result, dungeon_num)
        elif dungeon_num in config.DUNGEONS_LATE:
            await _fight_late_dungeon(message, user, dungeon_num)
        else:
            await message.answer("❌ Данжон не найден.")
        return

    # /dungeon invite @user — invite to multiplayer dungeon
    if subcmd == "invite":
        if message.reply_to_message:
            partner_id = message.reply_to_message.from_user.id
        elif len(args) >= 2:
            await message.answer("Ответьте на сообщение игрока /dungeon invite")
            return
        else:
            await message.answer("Ответьте на сообщение игрока /dungeon invite")
            return

        if partner_id == message.from_user.id:
            await message.answer("❌ Нельзя пригласить себя!")
            return

        # D10 is the only multiplayer dungeon
        result = await create_dungeon_invite(message.from_user.id, partner_id, 10)
        await message.answer(result["message"], parse_mode="HTML")
        return

    # /dungeon accept — accept multiplayer invite
    if subcmd == "accept":
        import time
        from game.dungeons import _dungeon_invites

        # Find invite for this user
        invite = None
        inviter_id = None
        for iid, inv in _dungeon_invites.items():
            if inv["partner_id"] == message.from_user.id:
                invite = inv
                inviter_id = iid
                break

        if not invite:
            await message.answer("❌ Нет активных приглашений.")
            return

        if time.time() > invite["timeout"]:
            del _dungeon_invites[inviter_id]
            await message.answer("❌ Приглашение истекло.")
            return

        dungeon_num = invite["dungeon_num"]
        del _dungeon_invites[inviter_id]

        if dungeon_num == 10:
            result = await fight_d10(inviter_id, message.from_user.id)
        else:
            result = await accept_dungeon_invite(message.from_user.id)

        if result.get("success"):
            await message.answer(result["message"], parse_mode="HTML")
        else:
            await message.answer(result["message"])
        return

    # /dungeon [number] — show info or fight specific dungeon
    # Handle "part2" suffix for D15
    part2 = False
    if len(args) >= 2 and args[1].lower() == "part2":
        part2 = True

    try:
        dungeon_num = int(subcmd)
    except ValueError:
        await message.answer(
            "Формат:\n"
            "  /dungeon — список подземелий\n"
            "  /dungeon fight — бой в данжоне вашей арены\n"
            "  /dungeon buy [номер] — купить ключ\n"
            "  /dungeon info [номер] — информация\n"
            "  /dungeon invite — пригласить игрока (D10)\n"
            "  /dungeon 15 part2 — вторая часть D15"
        )
        return

    # D15 — special wave-based dungeon
    if dungeon_num == 15:
        result = await fight_d15(message.from_user.id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    # D14 with dragon_round
    if dungeon_num == 14:
        dragon_round = 1
        if len(args) >= 2:
            try:
                dragon_round = int(args[1])
            except ValueError:
                pass
        ddata = config.DUNGEONS_LATE.get(14)
        if ddata:
            dungeon_data = _build_late_dungeon_data(ddata)
            result = await fight_standard_dungeon(
                message.from_user.id, dungeon_data,
                player_count=ddata["players"], dragon_round=dragon_round,
            )
            await _handle_fight_result(message, result, 14)
            return

    # Standard D1-D9
    if 1 <= dungeon_num <= 9:
        await _show_dungeon_info_detail(message, user, dungeon_num)
        return

    # D10+ late-game
    if dungeon_num in config.DUNGEONS_LATE:
        await _fight_late_dungeon(message, user, dungeon_num)
        return

    await message.answer(f"❌ Данжон {dungeon_num} не найден.")


# --- Helper functions ---

def _build_late_dungeon_data(ddata: dict) -> dict:
    """Build a dungeon dict compatible with fight_standard_dungeon from DUNGEONS_LATE."""
    return {
        "name": ddata["name"],
        "boss_emoji": ddata.get("boss_emoji", "🐉"),
        "hp_per_player": ddata["boss_hp"],
        "boss_atk": ddata["boss_atk"],
        "boss_def": ddata.get("boss_def", 0),
        "time_limit": ddata.get("time_limit_min", ddata["time_limit"]),
        "reward_min": ddata.get("reward_min", 100000),
        "reward_max": ddata.get("reward_max", 500000),
        "commands": ddata.get("commands", {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
        }),
    }


async def _handle_fight_result(message: Message, result: dict, dungeon_num: int):
    """Handle fight result, showing messages and follow-up options."""
    await message.answer(result["message"], parse_mode="HTML")

    # D14: second dragon
    if result.get("next_dragon"):
        await message.answer(
            f"🐉 Второй дракон готов!\n"
            f"Начать бой: /dungeon 14 2",
            parse_mode="HTML"
        )

    # D15: second part
    if result.get("next_part"):
        await message.answer(
            f"🐉 Дракон убегает с 0.1 HP!\n"
            f"Преследуйте: /dungeon 15 part2",
            parse_mode="HTML"
        )


async def _fight_late_dungeon(message: Message, user, dungeon_num):
    """Fight a late-game dungeon (D10+)."""
    ddata = config.DUNGEONS_LATE[dungeon_num]
    check_result = await _check_dungeon_requirements(message.from_user.id, dungeon_num, user)
    if not check_result["ok"]:
        await message.answer(check_result["message"], parse_mode="HTML")
        return

    dungeon_data = _build_late_dungeon_data(ddata)
    result = await fight_standard_dungeon(
        message.from_user.id, dungeon_data, player_count=ddata["players"],
    )
    await _handle_fight_result(message, result, dungeon_num)


async def _fight_d15_part2(message: Message, user):
    """Fight D15 part 2 (TIME Dragon TOP)."""
    ddata = config.DUNGEONS_LATE.get(15, {})
    part2 = ddata.get("second_part")
    if not part2:
        await message.answer("❌ Часть 2 D15 не найдена.")
        return

    check_result = await _check_dungeon_requirements(message.from_user.id, 15, user, part2=True)
    if not check_result["ok"]:
        await message.answer(check_result["message"], parse_mode="HTML")
        return

    dungeon_data = _build_late_dungeon_data(part2)
    result = await fight_standard_dungeon(
        message.from_user.id, dungeon_data, player_count=1, dungeon_part=2,
    )
    await message.answer(result["message"], parse_mode="HTML")


async def _show_dungeon_list(message: Message, user):
    """Show list of all available dungeons."""
    text = f"🏰 <b>Подземелья</b> — Area {user.area}\n\n"

    # D1-D9
    text += "📜 <b>Стандартные (D1-D9):</b>\n"
    text += "Купить ключ: /dungeon buy [номер]\n"
    text += "Бой: /dungeon fight\n\n"

    for dnum in range(1, 10):
        d = config.DUNGEONS.get(dnum)
        if not d:
            continue
        if dnum <= user.area:
            status = "✅"
        elif dnum == user.area + 1:
            status = "🔓"
        else:
            status = "🔒"

        cmds = list(d["commands"].keys())
        has_special = any(c.get("type") == "special" for c in d["commands"].values())
        special_note = " ⚡" if has_special else ""

        text += (
            f"  {status} <b>D{dnum}</b>: {d['boss_emoji']} {d['name']}{special_note}\n"
            f"    Ключ: 💰 {d['key_price']:,} | HP: {d['hp_per_player']}/player\n"
            f"    Награда: {d['reward_min']:,}-{d['reward_max']:,}\n"
            f"    Команды: {', '.join(cmds)}\n\n"
        )

    # D10+
    if user.area >= 10:
        text += "📜 <b>Поздние (D10+):</b>\n"
        for dnum, ddata in config.DUNGEONS_LATE.items():
            req = ddata["requirements"]
            players = ddata.get("players", 1)
            text += f"  /dungeon {dnum} — {ddata['name']} ({players}P, {ddata['time_limit']}min)\n"
            text += f"    {ddata['description']}\n\n"

        # D15 part 2 hint
        if user.area >= 15:
            text += "  /dungeon 15 part2 — TIME Dragon (TOP)\n\n"

    text += "Подробнее: /dungeon info [номер]"
    await message.answer(text, parse_mode="HTML")


async def _show_dungeon_info_detail(message: Message, user, dungeon_num):
    """Show detailed info for a specific dungeon."""
    # D1-D9
    if 1 <= dungeon_num <= 9:
        d = config.DUNGEONS.get(dungeon_num)
        if not d:
            await message.answer(f"❌ Данжон {dungeon_num} не найден.")
            return

        inv = await get_inventory(message.from_user.id)
        key_name = f"dungeon_{dungeon_num}_key"
        has_key = inv.get(key_name, 0) > 0

        text = (
            f"🏰 <b>D{dungeon_num}: {d['boss_emoji']} {d['name']}</b>\n\n"
            f"🔑 Ключ: 💰 {d['key_price']:,} монет\n"
            f"В инвентаре: {'✅ ' + str(inv.get(key_name, 0)) if has_key else '❌ Нет'}\n\n"
            f"🐉 <b>Босс:</b>\n"
            f"  HP: {d['hp_per_player']}/player\n"
            f"  ATK: {d['boss_atk']}\n"
            f"  DEF: {d['boss_def']}\n\n"
            f"⏱️ Лимит: {d['time_limit']} мин на игрока\n"
            f"💰 Награда: {d['reward_min']:,}-{d['reward_max']:,}\n\n"
            f"⚔️ <b>Команды:</b>\n"
        )

        for cmd_name, cmd_data in d["commands"].items():
            if cmd_data["type"] == "attack":
                hit_pct = int(cmd_data["chance"] * 100)
                text += f"  <code>{cmd_name}</code> — {hit_pct}% | ×{cmd_data['multiplier']} AT\n"
            elif cmd_data["type"] == "heal":
                hit_pct = int(cmd_data["chance"] * 100)
                heal_pct = int(cmd_data["heal_pct"] * 100)
                text += f"  <code>{cmd_name}</code> — {hit_pct}% | +{heal_pct}% HP\n"
            elif cmd_data["type"] == "counter":
                hit_pct = int(cmd_data["chance"] * 100)
                text += f"  <code>{cmd_name}</code> — {hit_pct}% | ×{cmd_data['counter_multiplier']} контратака\n"
            elif cmd_data["type"] == "special":
                hit_pct = int(cmd_data["chance"] * 100)
                effect = cmd_data.get("effect", "")
                if effect == "orb":
                    text += f"  <code>{cmd_name}</code> — {hit_pct}% | собрать орб (нужно 12)\n"
                elif effect == "puzzle":
                    text += f"  <code>{cmd_name}</code> — {hit_pct}% | загадка → урон\n"
                elif effect == "heal_boss":
                    text += f"  <code>{cmd_name}</code> — {hit_pct}% | исцеление дракона\n"

        text += f"\n📝 {d['description']}\n\n"

        if has_key:
            text += f"Начать бой: /dungeon fight"
        else:
            text += f"Купить ключ: /dungeon buy {dungeon_num}"

        await message.answer(text, parse_mode="HTML")
        return

    # D10+
    if dungeon_num in config.DUNGEONS_LATE:
        ddata = config.DUNGEONS_LATE[dungeon_num]
        req = ddata["requirements"]
        text = (
            f"🏰 <b>{ddata['name']}</b>\n\n"
            f"👥 Игроков: {ddata['players']}\n"
            f"⏱️ Лимит: {ddata['time_limit']} мин\n"
            f"🐉 HP: {ddata['boss_hp']} | ATK: {ddata['boss_atk']}\n\n"
            f"📝 {ddata['description']}\n\n"
            f"Требования:\n"
        )
        if "time_travel" in req:
            text += f"  ⏳ {req['time_travel']} Time Travel\n"
        if "gear" in req:
            gear_info = config.DUNGEON_GEAR_TIERS.get(req["gear"], {})
            text += f"  ⚔️ {gear_info.get('name', req['gear'])} снаряжение\n"
        if req.get("dungeon_key"):
            text += "  🔑 Dungeon key (или лошадь Тир VI+)\n"
        if "pets_required" in req:
            for pt, ptier in req["pets_required"].items():
                text += f"  🐾 {pt} Tier {ptier}+\n"

        if ddata["players"] > 1:
            text += "\nДля приглашения: /dungeon invite (ответьте на сообщение игрока)"
        else:
            text += f"\nНачать: /dungeon {dungeon_num}"

        await message.answer(text, parse_mode="HTML")
        return

    await message.answer(f"❌ Данжон {dungeon_num} не найден.")


async def _show_dungeon_info(message: Message, user):
    """Show general dungeon info."""
    text = f"🏰 <b>Подземелья — Подробности</b>\n\n"

    for dnum in range(1, min(user.area + 2, 16)):
        if 1 <= dnum <= 9:
            d = config.DUNGEONS.get(dnum)
            if d:
                has_special = any(c.get("type") == "special" for c in d["commands"].values())
                text += f"  <b>D{dnum}</b>: {d['boss_emoji']} {d['name']}{' ⚡' if has_special else ''}\n"
                text += f"    Ключ: {d['key_price']:,} | HP: {d['hp_per_player']}/player\n"
                text += f"    Награда: {d['reward_min']:,}-{d['reward_max']:,}\n\n"
        elif dnum in config.DUNGEONS_LATE:
            ddata = config.DUNGEONS_LATE[dnum]
            req = ddata["requirements"]
            text += f"\n  <b>{ddata['name']}</b> ({ddata['players']}P, {ddata['time_limit']}min)\n"
            text += f"  {ddata['description']}\n"
            text += "  Требования:\n"
            if "time_travel" in req:
                text += f"    ⏳ {req['time_travel']} Time Travel\n"
            if "gear" in req:
                gear_info = config.DUNGEON_GEAR_TIERS.get(req["gear"], {})
                text += f"    ⚔️ {gear_info.get('name', req['gear'])} снаряжение\n"
            if req.get("dungeon_key"):
                text += "    🔑 Dungeon key (или лошадь Тир VI+)\n"
            if "pets_required" in req:
                for pt, ptier in req["pets_required"].items():
                    text += f"    🐾 {pt} Tier {ptier}+\n"

    await message.answer(text, parse_mode="HTML")


async def _check_dungeon_requirements(user_id: int, dungeon_num: int, user, part2=False) -> dict:
    """Check if player meets dungeon requirements."""
    if part2:
        ddata = config.DUNGEONS_LATE.get(15, {}).get("second_part", {})
    else:
        ddata = config.DUNGEONS_LATE.get(dungeon_num, {})

    req = ddata.get("requirements", {})
    missing = []

    if "time_travel" in req:
        if user.tt_count < req["time_travel"]:
            missing.append(f"⏳ Time Travel: {user.tt_count}/{req['time_travel']}")

    if "gear" in req:
        gear_tier = req["gear"]
        gear_info = config.DUNGEON_GEAR_TIERS.get(gear_tier, {})
        eq = await get_equipment(user_id)
        weapon_tier = eq.get("weapon_tier", 1)
        armor_tier = eq.get("armor_tier", 1)
        min_tier = gear_info.get("weapon_min", 50)
        if weapon_tier < min_tier or armor_tier < min_tier:
            missing.append(f"⚔️ Снаряжение: {gear_info.get('name', gear_tier)} (нужно Тир {min_tier}+)")

    inv = await get_inventory(user_id)
    has_key = inv.get("dungeon_key", 0) > 0
    async with async_session() as s:
        horse = await s.get(Horse, user_id)
        has_horse_tier = False
        if horse:
            horse_tier_req = req.get("horse_tier", 6)
            has_horse_tier = horse.level >= horse_tier_req

    if req.get("dungeon_key") and not has_key and not has_horse_tier:
        missing.append("🔑 Dungeon key (или лошадь Тир VI+)")

    if "pets_required" in req:
        async with async_session() as s:
            result = await s.execute(
                select(Pet).where(Pet.user_id == user_id)
            )
            user_pets = {p.pet_type: p.pet_tier for p in result.scalars().all()}
            for pet_type, required_tier in req["pets_required"].items():
                tiers_order = ["I", "II", "III"]
                user_tier = user_pets.get(pet_type)
                if not user_tier or tiers_order.index(user_tier) < tiers_order.index(required_tier):
                    missing.append(f"🐾 {pet_type} Tier {required_tier}+")

    if missing:
        text = f"❌ <b>Требования для {ddata.get('name', f'D{dungeon_num}')}:</b>\n\n"
        text += "\n".join(f"  {m}" for m in missing)
        return {"ok": False, "message": text}

    return {"ok": True, "message": ""}
