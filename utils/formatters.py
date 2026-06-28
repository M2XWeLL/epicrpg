from config import TIER_NAMES


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n:,}"
    if n >= 1_000:
        return f"{n:,}"
    return str(n)


# ---------------------------------------------------------------------------
# /profile
# ---------------------------------------------------------------------------
def format_profile(user_data: dict, lang: str = "en") -> str:
    username = user_data.get("username", "Unknown")
    level = user_data.get("level", 1)
    xp = user_data.get("xp", 0)
    xp_needed = user_data.get("xp_needed", 1)
    coins = user_data.get("coins", 0)
    epic_coins = user_data.get("epic_coins", 0)
    bank = user_data.get("bank", 0)
    area = user_data.get("area", 1)
    max_area = user_data.get("max_area", 1)
    tt_count = user_data.get("tt_count", 0)
    atk = user_data.get("atk", 0)
    def_ = user_data.get("def", 0)
    weapon_tier = user_data.get("weapon_tier", 1)
    armor_tier = user_data.get("armor_tier", 1)
    hp = user_data.get("hp", 100)
    max_hp = user_data.get("max_hp", 100)
    coolness = user_data.get("coolness", 0)
    horse_tier = user_data.get("horse_tier", 1)
    horse_type = user_data.get("horse_type", "")
    title = user_data.get("title", "")

    xp_pct = xp / xp_needed * 100 if xp_needed > 0 else 0
    weapon_name = _weapon_name(weapon_tier)
    armor_name = _armor_name(armor_tier)
    horse_emoji = _horse_tier_emoji(horse_tier)
    type_name = horse_type.replace("_", " ").title() if horse_type else "Normal"

    text = f"<b>{username}</b>\n\n"
    if title:
        text += f"{title}\n\n"

    rank = user_data.get("rank", "10000+")

    xp_pct = xp / xp_needed * 100 if xp_needed > 0 else 0
    weapon_name = _weapon_name(weapon_tier)
    armor_name = _armor_name(armor_tier)
    horse_emoji = _horse_tier_emoji(horse_tier)
    type_name = horse_type.replace("_", " ").title() if horse_type else ("Нормальная" if lang == "ru" else "Normal")

    text = f"<b>{username}</b>\n\n"
    if title:
        text += f"{title}\n\n"

    if lang == "ru":
        text += (
            f"ПРОГРЕСС\n"
            f"Уровень: {level} (<code>{xp_pct:.2f}%</code>)\n"
            f"Опыт: <code>{xp:,}/{xp_needed:,}</code>\n"
            f"Зона: {area} (Макс: {max_area})\n"
            f"Путешествия во времени: {tt_count}\n"
            f"Крутость: {coolness}\n\n"
            f"ХАРАКТЕРИСТИКИ\n"
            f"АТК: {atk}\n"
            f"ЗАЩ: {def_}\n"
            f"ЖИЗНЬ: {hp}/{max_hp}\n\n"
            f"СНАРЯЖЕНИЕ\n"
            f"{weapon_name} [{_tier_label(weapon_tier)}]\n"
            f"{armor_name} [{_tier_label(armor_tier)}]\n"
            f"{horse_emoji} [{type_name}]\n\n"
            f"ДЕНЬГИ\n"
            f"Монеты: {coins:,}\n"
            f"EPIC монеты: {epic_coins}\n"
            f"Банк: {bank:,}\n\n"
            f"Рейтинг: {rank}"
        )
    else:
        text += (
            f"PROGRESS\n"
            f"Level: {level} (<code>{xp_pct:.2f}%</code>)\n"
            f"XP: <code>{xp:,}/{xp_needed:,}</code>\n"
            f"Area: {area} (Max: {max_area})\n"
            f"Time travels: {tt_count}\n"
            f"Coolness: {coolness}\n\n"
            f"STATS\n"
            f"ATK: {atk}\n"
            f"DEF: {def_}\n"
            f"LIFE: {hp}/{max_hp}\n\n"
            f"EQUIPMENT\n"
            f"{weapon_name} [{_tier_label(weapon_tier)}]\n"
            f"{armor_name} [{_tier_label(armor_tier)}]\n"
            f"{horse_emoji} [{type_name}]\n\n"
            f"MONEY\n"
            f"Coins: {coins:,}\n"
            f"EPIC coins: {epic_coins}\n"
            f"Bank: {bank:,}\n\n"
            f"Rank: {rank}"
        )
    return text


def _tier_label(tier: int) -> str:
    if tier >= 500: return "GODLY"
    if tier >= 200: return "ULTRA-OMEGA"
    if tier >= 100: return "OMEGA"
    if tier >= 70: return "ULTRA-EDGY"
    if tier >= 50: return "EDGY"
    if tier >= 40: return "Mythic"
    if tier >= 30: return "Legendary"
    if tier >= 20: return "Insane"
    if tier >= 10: return "Powerful"
    if tier >= 5: return "Strong"
    return "Basic"


def _weapon_name(tier: int) -> str:
    if tier >= 500: return "GODLY sword"
    if tier >= 200: return "ULTRA-OMEGA sword"
    if tier >= 100: return "OMEGA sword"
    if tier >= 70: return "ULTRA-EDGY sword"
    if tier >= 50: return "EDGY sword"
    if tier >= 20: return "electronical sword"
    if tier >= 17: return "coin sword"
    if tier >= 14: return "hair sword"
    if tier >= 11: return "unicorn sword"
    if tier >= 8: return "ruby sword"
    if tier >= 6: return "zombie sword"
    if tier >= 4: return "apple sword"
    if tier >= 3: return "wolf sword"
    if tier >= 2: return "fish sword"
    return "basic sword"


def _armor_name(tier: int) -> str:
    if tier >= 500: return "GODLY cookie"
    if tier >= 200: return "ULTRA-OMEGA armor"
    if tier >= 100: return "OMEGA armor"
    if tier >= 70: return "ULTRA-EDGY armor"
    if tier >= 50: return "EDGY armor"
    if tier >= 20: return "electronical armor"
    if tier >= 17: return "mermaid armor"
    if tier >= 14: return "coin armor"
    if tier >= 11: return "ruby armor"
    if tier >= 8: return "EPIC armor"
    if tier >= 6: return "banana armor"
    if tier >= 4: return "eye armor"
    if tier >= 3: return "wolf armor"
    if tier >= 2: return "fish armor"
    return "basic armor"


def _horse_tier_emoji(tier: int) -> str:
    return "🐴"


def _calc_rank(level: int, tt_count: int) -> str:
    score = level + tt_count * 10
    if score >= 500: return "#1"
    if score >= 300: return "#100"
    if score >= 200: return "#500"
    if score >= 100: return "#1000"
    return "10000+"


# ---------------------------------------------------------------------------
# /inventory
# ---------------------------------------------------------------------------
def format_inventory(user_data: dict, lang: str = "en") -> str:
    materials = user_data.get("materials", {})
    username = user_data.get("username", "Unknown")

    consumable_keys = [
        "life_potion", "arenacookie", "timecookie", "epic_berries",
        "common_lootbox", "uncommon_lootbox", "rare_lootbox", "epic_lootbox",
        "edgy_lootbox", "omega_lootbox", "lotteryticket", "seed", "dungeon_key",
    ]

    if lang == "ru":
        text = f"<b>{username} — инвентарь</b>\n\n"
        text += "<b>Предметы</b>\n"
        for mat, amt in sorted(materials.items()):
            if amt > 0 and mat not in consumable_keys:
                name = mat.replace("_", " ")
                text += f"  {name}: {amt:,}\n"

        text += "\n<b>Расходники</b>\n"
        for mat, amt in sorted(materials.items()):
            if amt > 0 and mat in consumable_keys:
                name = mat.replace("_", " ")
                text += f"  {name}: {amt:,}\n"
    else:
        text = f"<b>{username} — inventory</b>\n\n"
        text += "<b>Items</b>\n"
        for mat, amt in sorted(materials.items()):
            if amt > 0 and mat not in consumable_keys:
                name = mat.replace("_", " ")
                text += f"  {name}: {amt:,}\n"

        text += "\n<b>Consumables</b>\n"
        for mat, amt in sorted(materials.items()):
            if amt > 0 and mat in consumable_keys:
                name = mat.replace("_", " ")
                text += f"  {name}: {amt:,}\n"

    return text


# ---------------------------------------------------------------------------
# /horse
# ---------------------------------------------------------------------------
def format_horse(horse_data: dict) -> str:
    name = horse_data.get("name", "Horse")
    tier = horse_data.get("tier", 1)
    level = horse_data.get("level", 1)
    horse_type = horse_data.get("horse_type", "normal")
    epicness = horse_data.get("epicness", 0)
    fail_count = horse_data.get("fail_count", 0)
    max_level = tier * 10

    type_name = horse_type.replace("_", " ").title()

    boosts = _get_tier_boosts(tier)
    boost_text = ""
    for boost_name in boosts:
        boost_text += f"  • {boost_name}\n"

    text = (
        f"<b>{name}</b>\n\n"
        f"Horse Tier - {_tier_roman(tier)} 🐴\n"
        f"Horse Type - {type_name}\n"
        f"Horse Boost - {_get_type_boost_desc(horse_type)}\n"
        f"Horse Level - {level}/{max_level}\n"
        f"Horse Epicness - {epicness}/99\n"
        f"Horse fail count - {fail_count}\n\n"
        f"Tier Boosts:\n"
        f"{boost_text}\n"
        f"Horse commands\n"
        f"horse training - train your horse and it will level up\n"
        f"horse breeding [@player] - breed your horse with another player's one\n"
        f"horse race - join the next horse race (requires a horse tier V or higher)\n"
        f"horse feed - feed your horse with a carrot to change to a random new name"
    )
    return text


def _tier_roman(tier: int) -> str:
    romans = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
              6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
    return romans.get(tier, str(tier))


def _horse_type_emoji(horse_type: str) -> str:
    types = {"normal": "🐴", "defender": "🛡️", "strong": "💪", "tank": "❤️",
             "golden": "✨", "magic": "🔮", "festive": "🎄", "special": "⭐", "super_special": "🌟"}
    return types.get(horse_type, "🐴")


def _get_type_boost_desc(horse_type: str) -> str:
    descs = {
        "normal": "No boost",
        "defender": "Increases your DEF",
        "strong": "Increases your ATK",
        "tank": "Increases your LIFE",
        "golden": "Boosts the COINS obtained",
        "magic": "Boosts your ENCHANTMENTS",
        "festive": "Increases the chance to find random events",
        "special": "Unlocks epic quest (15 waves) and gives a boost in it",
        "super_special": "Like SPECIAL, but with 100 waves",
    }
    return descs.get(horse_type, "No boost")


def _get_tier_boosts(tier: int) -> dict:
    boosts = {}
    if tier >= 2:
        pct = tier * 8.1
        boosts[f"{pct:.1f}% extra daily and weekly rewards"] = True
    if tier >= 3:
        boosts["Immortality (hunt, adventure)"] = True
    if tier >= 4:
        mult = 1 + (tier - 3) * 0.36
        boosts[f"x{mult:.2f} chance to drop lootboxes"] = True
    if tier >= 6:
        boosts["No key is required in dungeons"] = True
    if tier >= 7:
        mult = 1 + (tier - 6) * 0.30
        boosts[f"x{mult:.2f} chance to drop a monster item"] = True
    return boosts


# ---------------------------------------------------------------------------
# /professions
# ---------------------------------------------------------------------------
def format_professions(prof_data: dict) -> str:
    text = "<b>Professions</b>\n\n"

    professions = [
        ("worker", "🪵", "Increases the chance to get a better item with working commands"),
        ("crafter", "🔧", "There's a chance to keep part of the recipe after crafting an item"),
        ("lootboxer", "📦", "Buffs the bank bonus and reduces the coins required to level up a horse"),
        ("merchant", "💰", "Increases the prices of the items you sell"),
        ("enchanter", "✨", "Increases your chance to get a better enchantment"),
    ]

    for key, emoji, desc in professions:
        level = prof_data.get(f"{key}_level", 1)
        xp = prof_data.get(f"{key}_xp", 0)
        xp_needed = int(100 * (1.5 ** (level - 1)))

        markers = ""
        for ms in [5, 25, 50, 100]:
            markers += "✅" if level >= ms else "⬜"

        text += f"{emoji} <b>{key.title()}</b> Lv {level} | {markers}\n"
        text += f"{desc}\n"
        if level >= 100:
            text += "Ascended skill unlocked!\n"
        text += "\n"

    text += "Claim profession rewards once reaching level 5/25/50/100 in each profession!"
    return text


def format_profession_detail(key: str, prof_data: dict) -> str:
    info = {
        "worker": ("🪵", "Worker", "Get worker XP with working commands (chop, fish, pickup, mine)",
                   "Your worker level increases your chance of getting a better item with working commands",
                   "For each level after 100: Adds a chance to find other items in working commands"),
        "crafter": ("🔧", "Crafter", "Get crafter XP by crafting and dismantling",
                    "Your crafter level increases your chance to save 10% of a recipe while using craft",
                    "For each level after 100: Increases the percentage of items returned from the recipe"),
        "lootboxer": ("📦", "Lootboxer", "Get lootboxer XP by opening lootboxes",
                      "Your lootboxer level increases your bank bonus and reduces the coins required to level up your horse",
                      "For each level after 100: Increases the maximum level of your horse"),
        "merchant": ("💰", "Merchant", "Get merchant XP by selling and buying items (does not apply for keys, equipment and potions)",
                     "Your merchant level increases the coins you get when selling items",
                     "For each level after 100: Adds a small chance to get a dragon scale when selling monster drops"),
        "enchanter": ("✨", "Enchanter", "Get enchanter XP by enchanting swords and armors",
                      "Your enchanter level increases your chance to get a better enchantment",
                      "For each level after 100: Adds a chance to get the coins when enchanting, instead of losing them"),
    }

    if key not in info:
        return "❌ Profession not found."

    emoji, name, how, effect, bonus100 = info[key]
    level = prof_data.get(f"{key}_level", 1)
    xp = prof_data.get(f"{key}_xp", 0)
    xp_needed = int(100 * (1.5 ** (level - 1)))
    pct = (xp / xp_needed * 100) if xp_needed > 0 else 0

    markers = ""
    for ms in [5, 25, 50, 100]:
        markers += "✅" if level >= ms else "⬜"

    text = (
        f"{emoji} <b>{name}</b>\n"
        f"Level: {level} (<code>{pct:.2f}%</code>)\n"
        f"XP: {xp:,}/{xp_needed:,}\n\n"
        f"About this profession\n"
        f"{how}\n\n"
        f"{effect}\n\n"
        f"{bonus100}\n"
        f"See all your professions with \"professions\""
    )
    return text


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
def format_start(username: str, lang: str = "en") -> str:
    from data.translations import t
    return (
        f"<b>{t(lang, 'start_title')}</b>\n\n"
        f"{t(lang, 'start_welcome', name=username)}\n\n"
        f"{t(lang, 'start_purpose')}\n\n"
        f"<b>{t(lang, 'start_how')}</b>\n"
        f"🔹 {t(lang, 'start_hunt')}\n"
        f"🔹 {t(lang, 'start_heal')}\n\n"
        f"<b>{t(lang, 'start_items')}</b>\n"
        f"🔹 {t(lang, 'start_chop')}\n"
        f"🔹 {t(lang, 'start_shop')}\n"
        f"🔹 {t(lang, 'start_daily')}\n\n"
        f"<b>{t(lang, 'start_dungeons')}</b>\n"
        f"🔹 {t(lang, 'start_dungeon_text')}\n"
        f"🔹 {t(lang, 'start_area_text')}\n\n"
        f"<b>{t(lang, 'start_more')}</b>\n"
        f"🔹 {t(lang, 'start_help_text')}\n"
        f"🔹 {t(lang, 'start_vote')}\n"
        f"🔹 {t(lang, 'start_rules')}"
    )


# ---------------------------------------------------------------------------
# /cooldowns
# ---------------------------------------------------------------------------
def format_cooldowns(user_id: int, cd_data: dict) -> str:
    from datetime import datetime
    import config

    now = datetime.utcnow()
    text = "⏱️ <b>Cooldowns</b>\n\n"

    cooldowns_list = [
        ("hunt", "hunt_last"),
        ("adventure", "adventure_last"),
        ("chop", "chop_last"),
        ("fish", "fish_last"),
        ("mine", "mine_last"),
        ("arena", "last_arena"),
        ("duel", "last_duel"),
        ("training", "last_training"),
        ("farm", "last_farm"),
    ]

    for name, field in cooldowns_list:
        cd_time = cd_data.get(field)
        required = config.COOLDOWNS.get(name, 0)
        if cd_time and cd_time > datetime.min:
            elapsed = (now - cd_time).total_seconds()
            if elapsed < required:
                remaining = int(required - elapsed)
                m, s = divmod(remaining, 60)
                text += f"  {name}: ⏳ {m}m {s}s\n"
            else:
                text += f"  {name}: ✅ Ready\n"
        else:
            text += f"  {name}: ✅ Ready\n"

    return text


# ---------------------------------------------------------------------------
# /combat result
# ---------------------------------------------------------------------------
DROP_DISPLAY = {
    "wolfskin": ("🐺", "wolf skin"),
    "zombieeye": ("👁️", "zombie eye"),
    "unicornhorn": ("🦄", "unicorn horn"),
    "mermaid_hair": ("🧜", "mermaid hair"),
    "chip": ("🔧", "chip"),
    "dragonscale": ("🐉", "dragon scale"),
}


def format_combat_result(
    username: str = "Player",
    mob: dict = None,
    total_dmg_to_mob: int = 0,
    total_dmg_to_player: int = 0,
    mob_hp: int = 0,
    won: bool = False,
    coins: int = 0,
    xp: int = 0,
    drops: list = None,
    leveled_up: bool = False,
    new_level: int = 0,
    coins_lost: int = 0,
    current_hp: int = 0,
    max_hp: int = 100,
    **kwargs,
) -> str:
    from data.translations import t

    if drops is None:
        drops = []
    if mob is None:
        mob = {}

    mob_name = mob.get("name", "MONSTER")
    mob_emoji = mob.get("emoji", "👾")

    # Detect lang from username convention — default to "en"
    # The caller should pass lang if available; fallback to "en"
    lang = kwargs.get("lang", "en")

    if won:
        text = f"{t(lang, 'combat_kill', name=username, emoji=mob_emoji, mob=mob_name)}\n"
        text += f"{t(lang, 'combat_earned', coins=f'{coins:,}', xp=f'{xp:,}')}\n"
        text += t(lang, 'combat_lost_hp', dmg=f'{total_dmg_to_player:,}', hp=f'{current_hp:,}', max=f'{max_hp:,}')
        if drops:
            for drop_id in drops:
                drop_emoji, drop_name = DROP_DISPLAY.get(drop_id, ("•", drop_id))
                text += f"\n{t(lang, 'combat_got_drop', name=username, emoji=drop_emoji, item=drop_name)}"
        if leveled_up:
            text += f"\n🎉 {t(lang, 'combat_levelup', level=new_level)}"
    else:
        text = f"{t(lang, 'combat_defeated', name=username, emoji=mob_emoji, mob=mob_name)}\n"
        text += t(lang, 'combat_coins_lost', coins=f'{coins_lost:,}')
        if drops:
            for drop_id in drops:
                drop_emoji, drop_name = DROP_DISPLAY.get(drop_id, ("•", drop_id))
                text += f"\n{t(lang, 'combat_got_drop', name=username, emoji=drop_emoji, item=drop_name)}"

    return text


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------
def format_help(user_area: int = 1, lang: str = "en") -> str:
    from data.translations import t

    text = (
        f"⚔️ <b>{t(lang, 'help_title')}</b>\n"
        f"{t(lang, 'help_info')}\n"
        f"{t(lang, 'help_prefix')}\n"
        f"{t(lang, 'help_example')}\n\n"

        f"🏅 <b>{t(lang, 'help_progress')}</b> 🏅\n"
        "<code>profile</code>, <code>inventory</code>, <code>professions</code>, <code>cooldowns</code>, "
        "<code>quest</code>, <code>epic_quest</code>, <code>horse</code>, <code>top</code>, <code>title</code>, "
        "<code>achievements</code>, <code>boosts</code>, <code>artifacts</code>, <code>cards</code>\n\n"

        f"🗡️ <b>{t(lang, 'help_fighting')}</b> 🗡️\n"
        "<code>hunt</code>, <code>hunt_alone</code>, <code>adventure</code>, <code>heal</code>, <code>duel</code>, "
        "<code>dungeon</code>, <code>arena</code>, <code>miniboss</code>\n\n"

        f"💰 <b>{t(lang, 'help_economy')}</b> 💰\n"
        "<code>shop</code>, <code>lootbox</code>, <code>open</code>, <code>buy</code>, "
        "<code>sell</code>, <code>use</code>, <code>give</code>, "
        "<code>npc</code>, "
        "<code>epic shop</code>, <code>coins</code>, <code>life</code>\n\n"

        f"🏦 <b>{t(lang, 'help_bank')}</b> 🏦\n"
        "<code>bank</code>, <code>deposit</code>, <code>withdraw</code>\n\n"

        f"💍 <b>{t(lang, 'help_social')}</b> 💍\n"
        "<code>marry</code>, <code>divorce</code>, <code>hunt_together</code>\n\n"

        f"🛠 <b>{t(lang, 'help_working')}</b> 🛠\n"
        "<code>chop</code>, <code>fish</code>, <code>craft</code>, <code>dismantle</code>, "
        "<code>recipes</code>\n\n"

        f"🎲 <b>{t(lang, 'help_gambling')}</b> 🎲\n"
        "<code>dice</code>, <code>cups</code>, <code>blackjack</code>, <code>slots</code>, "
        "<code>cf</code>, <code>lottery</code>\n\n"

        f"💎 <b>{t(lang, 'help_rewards')}</b> 💎\n"
        "<code>daily</code>, <code>weekly</code>, <code>vote</code>, <code>code</code>, "
        "<code>donate</code>\n\n"

        f"🌍 <b>{t(lang, 'help_misc')}</b> 🌍\n"
        "<code>rules</code>, <code>bg</code>, <code>world</code>, <code>lang</code>\n\n"
    )

    area_cmds = {
        2: "enchant, area, training",
        3: "axe, net, pickup",
        4: "ladder, guild, farm",
        5: "mine, multidice, cook",
        6: "bowsaw, boat, pickaxe",
        7: "refine, big arena, alchemy",
        8: "tractor, wheel",
        9: "chainsaw, bigboat",
        10: "drill, minintboss",
        11: "time travel, forge, greenhouse",
        12: "dynamite, pets, ultraining, badge",
        13: "transmute, hunt hardmode",
        14: "adventure hardmode, big dice",
        15: "super time travel, transcend",
    }

    area_emojis = {
        2: "0️⃣2️⃣", 3: "0️⃣3️⃣", 4: "0️⃣4️⃣", 5: "0️⃣5️⃣",
        6: "0️⃣6️⃣", 7: "0️⃣7️⃣", 8: "0️⃣8️⃣", 9: "0️⃣9️⃣",
        10: "1️⃣0️⃣", 11: "1️⃣1️⃣", 12: "1️⃣2️⃣", 13: "1️⃣3️⃣",
        14: "1️⃣4️⃣", 15: "1️⃣5️⃣",
    }

    text += f"🐉 <b>{t(lang, 'help_unlocked')}</b> 🐉\n"
    for zone in sorted(area_cmds.keys()):
        emoji = area_emojis.get(zone, f"{zone:02d}")
        text += f"{emoji} {area_cmds[zone]}\n"

    return text
