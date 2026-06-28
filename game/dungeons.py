"""Dungeon system: D1-D9 standard, D10+ late-game.

D1-D9: Buy key → fight boss with special commands (BITE/STAB/POWER/etc.)
D10+: Late-game dungeons with unique mechanics
"""
import random
import math
import config


def get_dungeon(dungeon_num: int) -> dict | None:
    """Get dungeon data for D1-D9."""
    return config.DUNGEONS.get(dungeon_num)


def get_dungeon_for_area(area: int) -> dict | None:
    """Get the dungeon that unlocks the given area (area N → dungeon N-1).
    Area 2 unlocked by D1, area 3 by D2, etc."""
    dungeon_num = area - 1
    if dungeon_num < 1 or dungeon_num > 9:
        return None
    return config.DUNGEONS.get(dungeon_num)


def get_dungeon_commands(dungeon_num: int) -> dict:
    """Get available commands for a dungeon."""
    d = config.DUNGEONS.get(dungeon_num, {})
    return d.get("commands", {})


async def buy_dungeon_key(user_id: int, dungeon_num: int) -> dict:
    """Buy a dungeon key for the given dungeon."""
    d = config.DUNGEONS.get(dungeon_num)
    if not d:
        return {"success": False, "message": f"❌ Данжон {dungeon_num} не найден."}

    from database.crud import get_user, get_inventory, add_materials
    from database.engine import async_session
    from database.models import User

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "❌ Игрок не найден."}

    if user.coins < d["key_price"]:
        return {
            "success": False,
            "message": f"❌ Нужно {d['key_price']:,} монет. У вас: {user.coins:,}",
        }

    key_name = f"dungeon_{dungeon_num}_key"
    async with async_session() as s:
        u = await s.get(User, user_id)
        u.coins -= d["key_price"]
        await s.commit()
    await add_materials(user_id, key_name, 1)

    return {
        "success": True,
        "message": f"🔑 Ключ к {d['name']} куплен! ({d['key_price']:,} монет)",
    }


async def fight_standard_dungeon(user_id: int, dungeon_num, player_count: int = 1,
                                  dragon_round: int = 1, dungeon_part: int = 1) -> dict:
    """Fight a dungeon boss with pre-simulated combat.

    dungeon_num can be:
      - int: look up D1-D9 from config
      - dict: use pre-built dungeon data (for D10+ late game)

    Returns dict with:
      - success, victory, message
      - next_dragon: int if D14 has another dragon to fight
      - next_part: dict if D15 has a second part
      - time_limit: float (minutes) for display
    """
    if isinstance(dungeon_num, dict):
        d = dungeon_num
        dn = 0
    else:
        d = config.DUNGEONS.get(dungeon_num)
        dn = dungeon_num
        if not d:
            return {"success": False, "message": f"❌ Данжон {dungeon_num} не найден."}

    from game.player import calc_atk, calc_def
    from database.crud import get_user, get_equipment, get_inventory, remove_materials
    from database.engine import async_session
    from database.models import User

    user = await get_user(user_id)
    eq = await get_equipment(user_id)
    if not user:
        return {"success": False, "message": "❌ Игрок не найден."}

    # Check dungeon key (D1-D9 only)
    free_dungeon = False
    if dn > 0:
        from database.crud import has_active_returning_event
        if await has_active_returning_event(user_id):
            free_dungeon = True
        else:
            inv = await get_inventory(user_id)
            key_name = f"dungeon_{dn}_key"
            has_key = inv.get(key_name, 0) > 0
            if not has_key:
                return {
                    "success": False,
                    "message": f"❌ Нет ключа от {d['name']}.\n"
                               f"Купить: /dungeon buy {dn} ({d['key_price']:,} монет)",
                }
            await remove_materials(user_id, key_name, 1)

    # Player stats
    player_atk = calc_atk(user.level, eq.get("weapon_tier", 1))
    player_def = calc_def(user.level, eq.get("armor_tier", 1))
    player_max_hp = 100 + user.level * 5
    player_hp = player_max_hp

    # Boss stats — scale for dragon_round (D14 second dragon = 2x)
    boss_max_hp = d["hp_per_player"] * player_count
    boss_atk = d["boss_atk"]
    boss_def = d.get("boss_def", 0)

    if dragon_round > 1:
        boss_max_hp = math.floor(boss_max_hp * dragon_round)
        boss_atk = math.floor(boss_atk * dragon_round)

    boss_hp = boss_max_hp

    # Scale boss for multiplayer
    if player_count > 1:
        if player_count > 2:
            boss_hp = math.floor(boss_max_hp * (1 + 0.5 * (player_count - 2)))
        boss_atk = math.floor(d["boss_atk"] * (1 + 0.15 * (player_count - 1)))

    commands = d["commands"]
    time_limit = d.get("time_limit", 2.5) * player_count

    # Check for special mechanics
    has_orbs = any(c.get("effect") == "orb" for c in commands.values())
    has_puzzle = any(c.get("effect") == "puzzle" for c in commands.values())
    has_heal_boss = any(c.get("effect") == "heal_boss" for c in commands.values())

    orbs_collected = 0
    orb_required = d.get("orb_count", 10) if has_orbs else 0
    boss_weakened = False

    log = []
    round_label = f" (дракон {dragon_round})" if dragon_round > 1 else ""
    part_label = f" — Часть {dungeon_part}" if dungeon_part > 1 else ""
    log.append(f"🏰 <b>{d['name']}{part_label}{round_label}</b> — {player_count}P")
    log.append(f"🐉 HP: {boss_max_hp} | ATK: {boss_atk} | DEF: {boss_def}")
    log.append(f"⚔️ Ваш ATK: {player_atk} | DEF: {player_def} | HP: {player_max_hp}")
    log.append(f"⏱️ Лимит: {time_limit:.1f} мин")
    if has_orbs:
        log.append(f"🔮 Орбы: 0/{orb_required} (соберите чтобы ослабить босса)")
    if has_puzzle:
        log.append(f"🧩 Ответьте на загадки чтобы нанести урон!")
    log.append("")

    # Random events
    boss_buffed = False
    boss_asleep = False
    boss_healed = False

    round_num = 0
    while player_hp > 0 and boss_hp > 0 and round_num < 50:
        round_num += 1

        # Random event check (5% chance after round 3, once per fight)
        if round_num > 3 and random.random() < 0.05 and not boss_buffed and not boss_asleep:
            event = random.choice(["potion", "apple", "sleep", "phase2"])
            if event == "potion":
                boss_hp = boss_max_hp
                boss_healed = True
                log.append(f"🐉 Раунд {round_num}: Дракон выпил зелье и восстановил ВСЁ HP!")
            elif event == "apple":
                boss_atk = math.floor(boss_atk * 1.5)
                boss_buffed = True
                log.append(f"🍎 Раунд {round_num}: Дракон съел яблоко! ATK ×1.5!")
            elif event == "sleep":
                boss_asleep = True
                boss_hp = 0
                log.append(f"😴 Раунд {round_num}: Дракон заснул! Автоматическая победа!")
                break
            elif event == "phase2":
                boss_hp = boss_max_hp
                boss_atk = math.floor(boss_atk * 2.5)
                boss_buffed = True
                log.append(f"💀 Раунд {round_num}: ФАЗА 2! ATK ×2.5! HP восстановлен!")

        # Player turn
        cmd_name, cmd_data = _select_command(commands)
        is_hit = random.random() < cmd_data["chance"]

        if cmd_data["type"] == "attack":
            if is_hit:
                effective_atk = max(1, player_atk - boss_def // 2)
                raw_dmg = math.floor(effective_atk * cmd_data["multiplier"])
                raw_dmg = math.floor(raw_dmg * random.uniform(0.9, 1.1))
                boss_hp -= raw_dmg
                log.append(f"⚔️ Раунд {round_num}: {cmd_name.upper()} — попал! -{raw_dmg} HP")
            else:
                log.append(f"❌ Раунд {round_num}: {cmd_name.upper()} — промах!")

        elif cmd_data["type"] == "heal":
            if is_hit:
                heal_amount = math.floor(player_max_hp * cmd_data["heal_pct"])
                player_hp = min(player_max_hp, player_hp + heal_amount)
                log.append(f"💚 Раунд {round_num}: HEAL — +{heal_amount} HP ({player_hp}/{player_max_hp})")
            else:
                log.append(f"❌ Раунд {round_num}: HEAL — промах!")

        elif cmd_data["type"] == "counter":
            if is_hit:
                effective_atk = max(1, player_atk - boss_def // 2)
                raw_dmg = math.floor(effective_atk * cmd_data["counter_multiplier"])
                raw_dmg = math.floor(raw_dmg * random.uniform(0.9, 1.1))
                boss_hp -= raw_dmg
                log.append(f"🛡️ Раунд {round_num}: DODGE — контратака! -{raw_dmg} HP")
            else:
                log.append(f"❌ Раунд {round_num}: DODGE — промах! Босс атакует свободно.")

        elif cmd_data["type"] == "special":
            effect = cmd_data.get("effect", "")

            if effect == "orb":
                if is_hit:
                    orbs_collected += 1
                    log.append(f"🔮 Раунд {round_num}: COLLECT ORB — {orbs_collected}/{orb_required}")
                    if orbs_collected >= orb_required and not boss_weakened:
                        boss_weakened = True
                        boss_hp = math.floor(boss_hp * 0.3)
                        boss_atk = math.floor(boss_atk * 0.5)
                        log.append(f"✨ Орбы собраны! Дракон ослаблен! HP×0.3, ATK×0.5")
                else:
                    log.append(f"❌ Раунд {round_num}: COLLECT ORB — промах!")

            elif effect == "puzzle":
                if is_hit:
                    trivia = _generate_puzzle()
                    effective_atk = max(1, player_atk - boss_def // 2)
                    trivia_dmg = math.floor(effective_atk * random.uniform(1.5, 3.0))
                    boss_hp -= trivia_dmg
                    log.append(f"🧩 Раунд {round_num}: PUZZLE «{trivia}» → -{trivia_dmg} HP!")
                else:
                    log.append(f"❌ Раунд {round_num}: PUZZLE — загадка не удалась!")

            elif effect == "heal_boss":
                if is_hit:
                    heal_amt = math.floor(boss_max_hp * 0.15)
                    boss_hp = min(boss_max_hp, boss_hp + heal_amt)
                    log.append(f"💚 Раунд {round_num}: HEAL DRAGON — +{heal_amt} HP боссу")
                else:
                    log.append(f"❌ Раунд {round_num}: HEAL DRAGON — не удалось!")

        # Boss turn
        if boss_hp > 0 and not boss_asleep:
            boss_dmg = max(1, boss_atk + random.randint(-boss_atk // 4, boss_atk // 4) - player_def // 3)
            player_hp -= boss_dmg
            log.append(f"🐉 Раунд {round_num}: Босс атакует! -{boss_dmg} HP ({max(0, player_hp)}/{player_max_hp})")

        if player_hp <= 0:
            break

    # --- Result ---
    result = {"success": True, "time_limit": time_limit}

    if boss_hp <= 0:
        coins = random.randint(d.get("reward_min", 10000), d.get("reward_max", 50000))
        xp = math.floor(coins * 0.6)

        from game.player import add_coins, add_xp
        await add_coins(user_id, coins)
        xp_result = await add_xp(user_id, xp)

        log.append("")
        log.append("🏆 <b>БОСС ПОВЕРЖЕН!</b>")
        log.append(f"💰 +{coins:,} монет | ⭐ +{xp:,} XP")
        if xp_result.get("leveled_up"):
            log.append(f"🎉 Уровень повышен! Level {xp_result['new_level']}!")
        if boss_healed:
            log.append("⚠️ Дракон восстанавливал HP!")
        if boss_buffed:
            log.append("⚠️ Дракон был усилен!")

        # D14: unlock second dragon
        if dn == 14 and dragon_round == 1:
            result["next_dragon"] = 2
            log.append("")
            log.append("🐉 Второй дракон приближается!")
            log.append("Начать бой: /dungeon fight")

        # D15: unlock part 2
        if dn == 15 and dungeon_part == 1 and "second_part" in config.DUNGEONS_LATE.get(15, {}):
            result["next_part"] = config.DUNGEONS_LATE[15]["second_part"]
            log.append("")
            log.append("🐉 Дракон убегает с 0.1 HP!")
            log.append("Преследуйте: /dungeon 15 part2")

        # D1-D9: unlock next area
        if 1 <= dn <= 9:
            next_area = dn + 1
            async with async_session() as s:
                u = await s.get(User, user_id)
                if u and u.area < next_area and next_area <= config.MAX_AREA:
                    u.area = next_area
                    if next_area > u.max_area:
                        u.max_area = next_area
                    await s.commit()
            if next_area <= config.MAX_AREA:
                log.append(f"🔓 Открыта локация: Area {next_area}!")

        result["victory"] = True

        # Quest hook — dungeon clear auto-cancels active quest (wiki)
        from game.quest import check_dungeon_cancel
        cancel_msg = await check_dungeon_cancel(user_id)
        if cancel_msg:
            log.append(f"\n{cancel_msg}")
    else:
        log.append("")
        log.append("💀 <b>ПОРАЖЕНИЕ</b>")
        log.append("Дракон оказался слишком сильным...")
        log.append("Вы потеряли ключ и вышли с 1 HP.")
        log.append("Используйте /heal чтобы восстановиться.")
        result["victory"] = False

    result["message"] = "\n".join(log)
    return result


def _select_command(commands: dict) -> tuple[str, dict]:
    """Select a command weighted by chance."""
    entries = list(commands.items())
    weights = [cmd["chance"] for _, cmd in entries]
    chosen_idx = random.choices(range(len(entries)), weights=weights, k=1)[0]
    return entries[chosen_idx]


def _generate_puzzle() -> str:
    """Generate a simple Epic RPG trivia/math puzzle."""
    puzzles = [
        "2 + 2", "10 - 3", "5 * 4", "100 / 5", "15 + 27",
        "9 * 9", "50 - 18", "7 * 8", "144 / 12", "25 * 4",
        "Сколько HP у D1? 50", "Какая команда шансом 5%? Epic Punch",
        "Сколько ключ стоит D9? 2.5M", "Какой ATK у D4? 143",
        "Сколько орбов нужно для D12? 10",
    ]
    return random.choice(puzzles)


# --- D10+ late game ---

async def start_dungeon(user_id: int, area: int) -> dict:
    """Start a dungeon run (D10+ late-game)."""
    from game.areas import get_area
    user_area_data = get_area(area)
    if not user_area_data:
        return {"success": False, "message": "Локация не найдена."}

    from game.player import calc_atk, calc_def
    from database.crud import get_user, get_equipment

    user = await get_user(user_id)
    eq = await get_equipment(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    atk = calc_atk(user.level, eq.get("weapon_tier", 1))
    def_ = calc_def(user.level, eq.get("armor_tier", 1))

    return {
        "success": True,
        "boss_name": user_area_data.get("dungeon", "Boss"),
        "boss_hp": user_area_data.get("base_hp", 300),
        "boss_atk": user_area_data.get("base_atk", 15),
        "boss_def": user_area_data.get("base_def", 5),
        "player_atk": atk,
        "player_def": def_,
        "player_hp": 100 + user.level * 5,
        "area": area,
    }


async def fight_dungeon_boss(user_id: int, state: dict, player_count: int = 1) -> dict:
    """Resolve dungeon boss fight (D10+ legacy)."""
    from game.combat import calc_damage, calc_dungeon_boss_coop
    from game.player import add_xp, add_coins
    from database.crud import get_user
    from database.engine import async_session
    from database.models import User

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    atk = state["player_atk"]
    def_ = state["player_def"]
    hp = state["player_hp"]

    boss_stats = calc_dungeon_boss_coop(state["boss_hp"], state["boss_atk"], player_count)
    boss_hp = boss_stats["hp"]
    boss_atk = boss_stats["atk"]
    boss_def = state["boss_def"]

    log = []
    for round_num in range(1, 11):
        dmg = calc_damage(atk, boss_def)
        boss_hp -= dmg
        log.append(f"Раунд {round_num}: Вы наносите {dmg} урона.")
        if boss_hp <= 0:
            break
        dmg_taken = calc_damage(boss_atk, def_)
        hp -= dmg_taken
        log.append(f"Раунд {round_num}: Босс наносит вам {dmg_taken} урона.")
        if hp <= 0:
            break

    if boss_hp <= 0:
        coins = state["area"] * random.randint(50, 100)
        xp = state["area"] * random.randint(60, 120)
        await add_coins(user_id, coins)
        xp_result = await add_xp(user_id, xp)
        async with async_session() as s:
            u = await s.get(User, user_id)
            if u and u.area < state["area"] + 1 and state["area"] + 1 <= config.MAX_AREA:
                u.area = state["area"] + 1
                if state["area"] + 1 > u.max_area:
                    u.max_area = state["area"] + 1
                await s.commit()
        msg = "\n".join(log)
        msg += f"\n\n🏆 Босс повержен!\n💰 +{coins} монет\n⭐ +{xp} XP"
        msg += f"\n🔓 Открыта новая локация: Area {state['area'] + 1}!"
        if xp_result.get("leveled_up"):
            msg += f"\n🎉 Уровень повышен! Level {xp_result['new_level']}!"
        # Quest hook — dungeon clear auto-cancels active quest
        from game.quest import check_dungeon_cancel
        cancel_msg = await check_dungeon_cancel(user_id)
        if cancel_msg:
            msg += f"\n{cancel_msg}"
        return {"success": True, "victory": True, "message": msg}
    else:
        msg = "\n".join(log)
        msg += "\n\n💀 Босс оказался слишком сильным..."
        return {"success": True, "victory": False, "message": msg}


# --- D10: Scripted 2-Player Dungeon ---
# Both players need full edgy set. Attacker charges sword x20 then attacks.
# Defender follows a specific spell sequence. Dragon has 1 HP.

async def fight_d10(inviter_id: int, partner_id: int) -> dict:
    """Scripted D10 fight per wiki.

    Attacker: Charge Edgy Sword x20, then Attack
    Defender: Weakness Spell, Protect, Charge Edgy Armor x2, Protect (until 10HP),
             Invulnerability, Healing Spell, Protect x5

    Dragon has 1 HP but attacking too early or overcharging = failure.
    """
    from database.crud import get_user, get_equipment
    from database.engine import async_session
    from database.models import User

    inviter = await get_user(inviter_id)
    partner = await get_user(partner_id)
    if not inviter or not partner:
        return {"success": False, "message": "❌ Игрок не найден."}

    inviter_eq = await get_equipment(inviter_id)
    partner_eq = await get_equipment(partner_id)

    # Check both have edgy gear (tier >= 50)
    for uid, name, eq in [(inviter_id, inviter.username or str(inviter_id), inviter_eq),
                          (partner_id, partner.username or str(partner_id), partner_eq)]:
        wt = eq.get("weapon_tier", 1)
        at = eq.get("armor_tier", 1)
        if wt < 50 or at < 50:
            return {
                "success": False,
                "message": f"❌ {name} не имеет полного edgy набора (нужно Edgy Sword + Edgy Armor).",
            }

    log = []
    log.append("🏰 <b>Dungeon 10 — EDGY Dragon</b>")
    log.append("👥 2 игрока | 📜 Скриптовый бой\n")

    # Assign roles randomly
    import random
    if random.random() < 0.5:
        attacker_id, attacker_name = inviter_id, inviter.username or str(inviter_id)
        defender_id, defender_name = partner_id, partner.username or str(partner_id)
    else:
        attacker_id, attacker_name = partner_id, partner.username or str(partner_id)
        defender_id, defender_name = inviter_id, inviter.username or str(inviter_id)

    log.append(f"⚔️ Атакующий: <b>{attacker_name}</b>")
    log.append(f"🛡️ Защитник: <b>{defender_name}</b>\n")

    dragon_hp = 1
    dragon_max_hp = 1
    defender_hp = 200
    defender_max_hp = 200
    attacker_hp = 200
    attacker_max_hp = 200
    charge = 0
    overcharged = False
    attacked_early = False
    defender_died = False

    log.append("🐉 <b>EDGY Dragon</b> — HP: 1 (не поддавайтесь!)")
    log.append("")

    # --- Attacker sequence: Charge x20, then Attack ---
    for i in range(1, 21):
        charge += 5  # 5% per charge
        if charge > 100:
            overcharged = True
            log.append(f"  ⚔️ Раунд {i}: {attacker_name} заряжает меч... {charge}% — <b>ПЕРЕЗАРЯДКА!</b>")
            break
        log.append(f"  ⚔️ Раунд {i}: {attacker_name} заряжает меч... {charge}%")

        # Dragon attacks each round
        dmg_to_defender = random.randint(8, 15)
        defender_hp -= dmg_to_defender
        dmg_to_attacker = random.randint(5, 10)
        attacker_hp -= dmg_to_attender

        if defender_hp <= 0:
            defender_died = True
            log.append(f"  🛡️ {defender_name} погибает на раунде {i}!")
            break
        if attacker_hp <= 0:
            log.append(f"  ⚔️ {attacker_name} погибает на раунде {i}!")
            break

    if overcharged:
        log.append(f"\n💀 <b>ПОРАЖЕНИЕ!</b> Перезарядка меча! Дракон уничтожает вас!")
        return {"success": True, "victory": False, "message": "\n".join(log)}

    if defender_died:
        log.append(f"\n💀 <b>ПОРАЖЕНИЕ!</b> Защитник погиб до завершения зарядки!")
        return {"success": True, "victory": False, "message": "\n".join(log)}

    # Attack at 100% charge
    log.append(f"\n  ⚔️ {attacker_name}: <b>АТАКА!</b> (100% заряд)")

    # Dragon has 1 HP — guaranteed kill if not overcharged
    dragon_hp = 0
    log.append(f"  🐉 EDGY Dragon повержен!\n")

    # --- Defender sequence (flavor text, doesn't affect outcome in simulation) ---
    log.append(f"🛡️ <b>Последовательность защитника:</b>")
    defender_sequence = [
        ("Weakness Spell", "削弱了 дракона"),
        ("Protect", "создал защитный барьер"),
        ("Charge Edgy Armor", "зарядил броню (1)"),
        ("Charge Edgy Armor", "зарядил броню (2)"),
        ("Protect", "поддерживает барьер"),
        ("Invulnerability", "стал неуязвимым"),
        ("Healing Spell", "восстановил HP"),
        ("Protect x5", "финальная защита"),
    ]
    for action, desc in defender_sequence:
        log.append(f"  🛡️ {defender_name}: {action} — {desc}")

    # --- Victory ---
    log.append("")
    log.append("🏆 <b>D10 ПОКОРЁН!</b>\n")

    # Rewards
    coins = random.randint(300000, 500000)
    xp = random.randint(100000, 200000)

    from game.player import add_coins, add_xp
    await add_coins(inviter_id, coins)
    await add_coins(partner_id, coins)
    xp1 = await add_xp(inviter_id, xp)
    xp2 = await add_xp(partner_id, xp)

    log.append(f"💰 +{coins:,} монет (каждый)")
    log.append(f"⭐ +{xp:,} XP (каждый)")
    if xp1.get("leveled_up"):
        log.append(f"🎉 {attacker_name} Level up! {xp1['new_level']}")
    if xp2.get("leveled_up"):
        log.append(f"🎉 {defender_name} Level up! {xp2['new_level']}")

    # Unlock area 11 for both
    async with async_session() as s:
        for uid in [inviter_id, partner_id]:
            u = await s.get(User, uid)
            if u and u.area < 11:
                u.area = 11
                if u.max_area < 11:
                    u.max_area = 11
            if u and u.max_area < 11:
                u.max_area = 11
        await s.commit()

    log.append(f"\n🔓 Открыта локация: Area 11!")

    # Quest hooks
    from game.quest import check_dungeon_cancel
    for uid in [inviter_id, partner_id]:
        cancel_msg = await check_dungeon_cancel(uid)
        if cancel_msg:
            log.append(f"\n{cancel_msg}")

    return {"success": True, "victory": True, "message": "\n".join(log)}


# --- Multiplayer dungeon invite system ---
# Stores pending dungeon invites in memory (lost on restart, acceptable for gameplay)
_dungeon_invites = {}  # {inviter_id: {"partner_id": int, "dungeon_num": int, "timeout": float}}


async def create_dungeon_invite(inviter_id: int, partner_id: int, dungeon_num: int) -> dict:
    """Create a dungeon invite for multiplayer (D10)."""
    import time

    _dungeon_invites[inviter_id] = {
        "partner_id": partner_id,
        "dungeon_num": dungeon_num,
        "timeout": time.time() + 120,  # 2 minutes to accept
    }

    from database.crud import get_user
    inviter = await get_user(inviter_id)
    partner = await get_user(partner_id)

    if not inviter or not partner:
        return {"success": False, "message": "❌ Игрок не найден."}

    inviter_name = inviter.username or str(inviter_id)
    partner_name = partner.username or str(partner_id)

    return {
        "success": True,
        "message": (
            f"🏰 <b>Приглашение в данжон!</b>\n\n"
            f"{inviter_name} приглашает {partner_name} в D10!\n"
            f"Принять: /dungeon accept"
        ),
    }


async def accept_dungeon_invite(partner_id: int) -> dict:
    """Accept a dungeon invite and start the fight."""
    import time

    invite = None
    inviter_id = None
    for iid, inv in _dungeon_invites.items():
        if inv["partner_id"] == partner_id:
            invite = inv
            inviter_id = iid
            break

    if not invite:
        return {"success": False, "message": "❌ Нет активных приглашений."}

    if time.time() > invite["timeout"]:
        del _dungeon_invites[inviter_id]
        return {"success": False, "message": "❌ Приглашение истекло."}

    dungeon_num = invite["dungeon_num"]
    del _dungeon_invites[inviter_id]

    # Build dungeon dict for the fight
    ddata = config.DUNGEONS_LATE.get(dungeon_num)
    if not ddata:
        return {"success": False, "message": "❌ Данжон не найден."}

    dungeon_data = {
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

    result = await fight_standard_dungeon(
        inviter_id, dungeon_data, player_count=2,
    )
    return result


# --- D15: Dungeon of the End (wave-based) ---

async def fight_d15(user_id: int) -> dict:
    """Fight D15: Dungeon of the End.

    Per wiki: 10 waves of enemies + final boss.
    30 players, each deals exactly 10 damage per round = 300 total/round.
    Boss heals 100 HP per round. No time limit.
    Solo simulation: player does 300 damage/round (simulating 30 players).
    """
    import json as _json
    from database.crud import get_user, add_materials

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "❌ Игрок не найден."}

    # Simulate 30-player group: each player does 10, total = 300/round
    GROUP_DMG = 300
    PLAYER_HP = 500  # generous HP for solo sim

    log = []
    log.append("🏰 <b>Dungeon of the End</b>")
    log.append("Финальное подземелье! 10 волн + Босс\n")

    # --- Waves 1-10 ---
    waves = config.D15_WAVES

    for wave_num, (name, emoji, hp, atk) in enumerate(waves, 1):
        wave_hp = hp
        rounds = 0
        log.append(f"⚔️ <b>Волна {wave_num}: {emoji} {name}</b> (HP: {hp:,})")

        for round_num in range(1, 201):
            wave_hp -= GROUP_DMG
            rounds = round_num

            if wave_hp <= 0:
                log.append(f"  💥 Волна {wave_num} пройдена! ({round_num} раундов)")
                break

            # Boss attacks (scaled for solo)
            raw = atk * random.uniform(0.9, 1.1)
            boss_dmg = max(1, math.floor(raw / 30))  # divide by 30 players
            PLAYER_HP -= boss_dmg

            if PLAYER_HP <= 0:
                log.append(f"  💀 Раунд {round_num}: Вас повержали!")
                log.append(f"\n💀 <b>ПОРАЖЕНИЕ!</b> Вы пали на волне {wave_num}.")
                return {"success": True, "victory": False, "message": "\n".join(log)}
        else:
            log.append(f"  ⏰ Волна {wave_num} не пройдена за 200 раундов!")
            return {"success": True, "victory": False, "message": "\n".join(log)}

    # --- Boss: Time Dragon ---
    boss = config.D15_BOSS
    boss_hp = boss["hp"]
    log.append(f"\n🐉 <b>ФИНАЛ: {boss['name']}!</b> (HP: {boss_hp:,})")
    log.append(f"  💚 Босс лечится {boss['heal_per_round']} HP/раунд (30 игроков × 10 = 300 урона/раунд)\n")

    for round_num in range(1, 301):
        # Group attacks (30 × 10 = 300)
        boss_hp -= GROUP_DMG

        if boss_hp <= 0:
            log.append(f"  💥 Раунд {round_num}: {boss['name']} повержен!")
            break

        # Boss heals (cap at max)
        boss_hp = min(boss["hp"], boss_hp + boss["heal_per_round"])

        # Boss attacks (scaled for solo)
        raw = boss["atk"] * random.uniform(0.9, 1.1)
        boss_dmg = max(1, math.floor(raw / 30))
        PLAYER_HP -= boss_dmg

        if PLAYER_HP <= 0:
            log.append(f"  💀 Раунд {round_num}: Вас повержали!")
            log.append(f"\n💀 <b>ПОРАЖЕНИЕ!</b> Босс оказался слишком силён.")
            return {"success": True, "victory": False, "message": "\n".join(log)}

        if round_num % 10 == 0:
            log.append(f"  ⏱️ Раунд {round_num}: Dragon HP {boss_hp:,} | Ваш HP {PLAYER_HP}")
    else:
        log.append(f"  ⏰ 300 раундов! Босс всё ещё жив.")
        return {"success": True, "victory": False, "message": "\n".join(log)}

    # --- Victory! ---
    log.append("")
    log.append("🏆 <b>DUNGEON OF THE END ПОКОРЁН!</b>\n")

    rewards = config.D15_REWARDS
    tokens = random.randint(rewards["arena_tokens_min"], rewards["arena_tokens_max"])
    epic_item = random.choice(rewards["epic_items"])
    item_id, qty_min, qty_max = epic_item
    qty = random.randint(qty_min, qty_max)

    await add_materials(user_id, "arenacookie", tokens)
    await add_materials(user_id, item_id, qty)

    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = _json.load(f)
    item_name = mat_data.get("names", {}).get(item_id, item_id)
    item_emoji = mat_data.get("emojis", {}).get(item_id, "❓")

    log.append("🎁 Награды:")
    log.append(f"  🍪 {tokens} Arena Cookies")
    log.append(f"  {item_emoji} {qty}x {item_name}")
    log.append("")
    log.append("🏅 Титул: <b>Dungeon Master</b>")

    return {"success": True, "victory": True, "message": "\n".join(log)}
