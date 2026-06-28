"""
Pet system — 19 pets, 25 tiers, skills with ranks, adventures, fusion, ascension.
Wiki-accurate pet score: tier * (tier + skill_score * rank_multiplier)
"""
import random
import json
from datetime import datetime, timedelta
import config
from config import PET_MAX_BASE, PET_RANK_ORDER, PET_RANK_MULT, PET_SKILL_SCORES

DATA_DIR = config.DATA_DIR


def _load() -> dict:
    with open(DATA_DIR / "pets.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ────────────────────────────────────────────
# Utility
# ────────────────────────────────────────────

def get_pet_info(pet_type: str) -> dict | None:
    data = _load()
    return data["pets"].get(pet_type)


def get_all_pets_list() -> list:
    data = _load()
    return [
        {"type": k, "name": v["name"], "emoji": v["emoji"], "score": v["base_score"]}
        for k, v in data["pets"].items()
    ]


def get_max_pets(tt_count: int) -> int:
    """Wiki: 5 base + 1 per time travel."""
    return PET_MAX_BASE + tt_count


def skill_rank_up(rank: str) -> str | None:
    """Return next rank or None if already SS+."""
    idx = PET_RANK_ORDER.index(rank) if rank in PET_RANK_ORDER else 0
    if idx < len(PET_RANK_ORDER) - 1:
        return PET_RANK_ORDER[idx + 1]
    return None


def pet_display(pet, data: dict | None = None) -> str:
    """Format a single pet for display."""
    if data is None:
        data = _load()
    info = data["pets"].get(pet.pet_type, {})
    emoji = info.get("emoji", "🐾")
    name = info.get("name", pet.pet_type)
    tier_num = config.pet_tier_to_num(pet.pet_tier)
    skill_score = PET_SKILL_SCORES.get(pet.skill, 0)
    rank_mult = PET_RANK_MULT.get(pet.skill_rank, 1)
    score = config.calc_pet_score(tier_num, pet.skill, pet.skill_rank)

    status_map = {"idle": "😴", "adventure": "⚔️", "tournament": "🏆"}
    status = status_map.get(pet.status, "😴")

    return (
        f"{emoji} <b>{name}</b> — Tier {pet.pet_tier} (Lv.{pet.pet_level})\n"
        f"   Skill: {pet.skill.title()} [{pet.skill_rank}] | "
        f"Score: {score} | Status: {status}"
    )


# ────────────────────────────────────────────
# Catch
# ────────────────────────────────────────────

def _get_catch_rates(area: int) -> dict:
    data = _load()
    if area <= 5:
        return data["catch_rates"]["area_1_5"]
    elif area <= 10:
        return data["catch_rates"]["area_6_10"]
    elif area <= 15:
        return data["catch_rates"]["area_11_15"]
    else:
        return data["catch_rates"]["area_16_plus"]


def _roll_pet(area: int) -> dict | None:
    """Roll for a pet catch. Returns pet dict or None."""
    data = _load()
    rates = _get_catch_rates(area)
    roll = random.random()

    if roll < rates["rare"]:
        pool = data["rare_pets"]
        rarity = "rare"
    elif roll < rates["rare"] + rates["uncommon"]:
        pool = data["uncommon_pets"]
        rarity = "uncommon"
    else:
        pool = data["common_pets"]
        rarity = "common"

    pet_type = random.choice(pool)
    info = data["pets"][pet_type]

    tier_roll = random.random()
    if tier_roll < 0.60:
        tier = "I"
    elif tier_roll < 0.90:
        tier = "II"
    else:
        tier = "III"

    tier_data = info["tiers"].get(tier, {"score": 1, "skill": "normie", "skill_name": "Normie"})
    tier_num = config.pet_tier_to_num(tier)
    score = config.calc_pet_score(tier_num, tier_data["skill"], "F")

    return {
        "pet_type": pet_type,
        "pet_tier": tier,
        "pet_score": score,
        "skill": tier_data["skill"],
        "skill_rank": "F",
        "name": info["name"],
        "emoji": info["emoji"],
        "rarity": rarity,
    }


async def catch_pet(user_id: int, area: int) -> dict:
    """Try to catch a pet. Enforces max pet limit."""
    from database.engine import async_session
    from database.models import Pet, User
    from sqlalchemy import select

    async with async_session() as s:
        user = await s.get(User, user_id)
        tt_count = user.tt_count if user else 0
        max_pets = get_max_pets(tt_count)

        count_result = await s.execute(
            select(Pet).where(Pet.user_id == user_id)
        )
        current_count = len(list(count_result.scalars().all()))

        if current_count >= max_pets:
            return {"caught": False, "reason": "max_pets"}

    pet = _roll_pet(area)
    if not pet:
        return {"caught": False}

    async with async_session() as s:
        new_pet = Pet(
            user_id=user_id,
            pet_type=pet["pet_type"],
            pet_tier=pet["pet_tier"],
            pet_score=pet["pet_score"],
            skill=pet["skill"],
            skill_rank="F",
            pet_level=1,
            status="idle",
        )
        s.add(new_pet)
        await s.commit()

    return {
        "caught": True,
        "pet_type": pet["pet_type"],
        "pet_tier": pet["pet_tier"],
        "pet_score": pet["pet_score"],
        "skill": pet["skill"],
        "name": pet["name"],
        "emoji": pet["emoji"],
        "rarity": pet["rarity"],
    }


# ────────────────────────────────────────────
# Info / Summary / Detail
# ────────────────────────────────────────────

async def pets_info(user_id: int) -> str:
    """Return the /pets info text."""
    from database.engine import async_session
    from database.models import Pet, User
    from sqlalchemy import select

    data = _load()

    async with async_session() as s:
        user = await s.get(User, user_id)
        tt_count = user.tt_count if user else 0
        result = await s.execute(
            select(Pet).where(Pet.user_id == user_id).order_by(Pet.pet_id)
        )
        pets = list(result.scalars().all())

    max_pets = get_max_pets(tt_count)

    if not pets:
        return (
            "🐾 <b>Питомцы</b>\n\n"
            "У вас нет питомцев. Попробуйте /training для поимки!\n"
            "Шанс поимки: 4% (10% с Tier IX лошадью, 20% с Tier X)\n\n"
            "Вместимость: 0/" + str(max_pets) + "\n\n"
            "Доступные питомцы:\n" +
            "\n".join(f"  {p['emoji']} {p['name']} ({p['type']}) — {p['score']} pts" for p in get_all_pets_list()[:10]) +
            "\n  ..."
        )

    text = f"🐾 <b>Питомцы</b> ({len(pets)}/{max_pets})\n\n"
    for p in pets:
        text += pet_display(p, data) + "\n"

    text += (
        "\n<b>Команды:</b>\n"
        "  /pets info — Информация\n"
        "  /pets detail [id] — Детали питомца\n"
        "  /pets summary — Сводка\n"
        "  /pets adventure find/learn/drill [ids] — Приключение\n"
        "  /pets adventure cancel [id] — Отменить приключение\n"
        "  /pets claim — Получить награду\n"
        "  /pets fusion [ids] — Слияние\n"
        "  /pets fusion automatic — Автослияние\n"
        "  /pets release [id] — Выпустить\n"
        "  /pets ascend — Аскенция\n"
        "  /pets tournament — Турнир"
    )
    return text


async def pets_summary(user_id: int) -> str:
    """Return summary of all pets."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(Pet.user_id == user_id)
        )
        pets = list(result.scalars().all())

    if not pets:
        return "🐾 У вас нет питомцев."

    total_score = sum(config.calc_pet_score(config.pet_tier_to_num(p.pet_tier), p.skill, p.skill_rank) for p in pets)
    tier_counts = {}
    skill_counts = {}
    rank_counts = {}
    for p in pets:
        tier_counts[p.pet_tier] = tier_counts.get(p.pet_tier, 0) + 1
        skill_counts[p.skill] = skill_counts.get(p.skill, 0) + 1
        rank_counts[p.skill_rank] = rank_counts.get(p.skill_rank, 0) + 1

    text = f"🐾 <b>Сводка питомцев</b>\n\nВсего: {len(pets)}\n"
    text += "Тиры: " + " | ".join(f"{t}: {c}" for t, c in sorted(tier_counts.items())) + "\n"
    text += f"Общий Score: {total_score}\n\n"

    text += "<b>Навыки:</b>\n"
    for skill, count in sorted(skill_counts.items(), key=lambda x: -x[1]):
        text += f"  {skill}: {count}\n"

    text += "\n<b>Ранги:</b>\n"
    for rank, count in sorted(rank_counts.items(), key=lambda x: -x[1]):
        text += f"  {rank}: {count}\n"

    return text


async def pets_detail(user_id: int, pet_id: int) -> str:
    """Detailed pet view with score breakdown."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    data = _load()

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(Pet.user_id == user_id, Pet.pet_id == pet_id)
        )
        pet = result.scalar_one_or_none()

    if not pet:
        return "❌ Питомец не найден. Используйте /pets для списка."

    info = data["pets"].get(pet.pet_type, {})
    emoji = info.get("emoji", "🐾")
    name = info.get("name", pet.pet_type)

    tier_num = config.pet_tier_to_num(pet.pet_tier)
    skill_score = PET_SKILL_SCORES.get(pet.skill, 0)
    rank_mult = PET_RANK_MULT.get(pet.skill_rank, 1)
    score = config.calc_pet_score(tier_num, pet.skill, pet.skill_rank)

    skill_desc = data["skills"].get(pet.skill, {}).get("desc", "Нет описания.")

    text = (
        f"{emoji} <b>{name}</b> (ID: {pet.pet_id})\n\n"
        f"📊 <b>Разбор Score:</b>\n"
        f"  Tier: {pet.pet_tier} (число: {tier_num})\n"
        f"  Skill: {pet.skill.title()} (score: {skill_score})\n"
        f"  Rank: {pet.skill_rank} (множитель: {rank_mult})\n"
        f"  Формула: {tier_num} × ({tier_num} + {skill_score} × {rank_mult})\n"
        f"  Score: <b>{score}</b>\n\n"
        f"📜 <b>{pet.skill.title()} [{pet.skill_rank}]:</b>\n  {skill_desc}\n\n"
        f"  Level: {pet.pet_level} | Status: {pet.status}"
    )

    if pet.status == "adventure" and pet.adventure_ready_at:
        remaining = pet.adventure_ready_at - datetime.utcnow()
        if remaining.total_seconds() > 0:
            mins = int(remaining.total_seconds() / 60)
            text += f"\n  ⏳ Возвращается через: {mins} мин"
        else:
            text += "\n  ✅ Приключение завершено! /pets claim"

    return text


# ────────────────────────────────────────────
# Adventure (3 types: find, learn, drill)
# ────────────────────────────────────────────

async def pets_adventure(user_id: int, adventure_type: str, pet_ids: list[str]) -> str:
    """Send pets on adventure. adventure_type: find/learn/drill. pet_ids: list of pet_id strings."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    if adventure_type not in ("find", "learn", "drill"):
        return "❌ Тип приключения: find, learn или drill."

    data = _load()
    adv_config = data["adventure"][adventure_type]
    duration = data["adventure"]["duration_hours"]

    async with async_session() as s:
        # Parse pet IDs
        pet_id_ints = []
        for pid in pet_ids:
            try:
                pet_id_ints.append(int(pid))
            except ValueError:
                continue

        if not pet_id_ints:
            # No IDs specified — pick best idle pet
            result = await s.execute(
                select(Pet).where(Pet.user_id == user_id, Pet.status == "idle").order_by(Pet.pet_score.desc())
            )
            all_idle = list(result.scalars().all())
            if not all_idle:
                return "❌ Нет свободных питомцев для приключения."
            selected = [all_idle[0]]
        else:
            result = await s.execute(
                select(Pet).where(Pet.user_id == user_id, Pet.status == "idle")
            )
            all_idle = {p.pet_id: p for p in result.scalars().all()}
            selected = []
            for pid in pet_id_ints:
                if pid in all_idle:
                    selected.append(all_idle[pid])

            if not selected:
                return "❌ Ни один из указанных питомцев не свободен."

        # Check EPIC skill: if first pet has epic, can send 2nd
        if len(selected) > 1:
            has_epic = selected[0].skill == "epic"
            if not has_epic:
                # Only send first
                selected = [selected[0]]

        # Check Time Traveler skill: chance instant return
        for pet in selected:
            if pet.skill == "time_traveler":
                rank_mult = PET_RANK_MULT.get(pet.skill_rank, 1)
                instant_chance = 0.10 * rank_mult / 9
                if random.random() < instant_chance:
                    # Will be handled at claim time
                    pass

        # Apply Fast skill: reduce duration
        adjusted_duration = duration
        for pet in selected:
            if pet.skill == "fast":
                rank_mult = PET_RANK_MULT.get(pet.skill_rank, 1)
                reduction_minutes = 9.6 * rank_mult  # 9m 36s per rank level
                adjusted_duration = max(1, adjusted_duration * 60 - reduction_minutes)
                adjusted_duration /= 60

        now = datetime.utcnow()
        ready_at = now + timedelta(hours=adjusted_duration)

        for pet in selected:
            pet.status = "adventure"
            pet.adventure_type = adventure_type
            pet.adventure_started_at = now
            pet.adventure_ready_at = ready_at

        await s.commit()

    lines = []
    for pet in selected:
        info = data["pets"].get(pet.pet_type, {})
        lines.append(f"  {info.get('emoji', '🐾')} {info.get('name', pet.pet_type)} (Tier {pet.pet_tier})")

    mins = int(adjusted_duration * 60)
    return (
        f"⚔️ <b>Приключение ({adventure_type})</b>\n\n"
        + "\n".join(lines) + "\n\n"
        f"Время: {mins} мин\n"
        f"Забрать: /pets claim"
    )


async def pets_adventure_cancel(user_id: int, pet_id: int) -> str:
    """Cancel a pet adventure and return it."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(Pet.user_id == user_id, Pet.pet_id == pet_id, Pet.status == "adventure")
        )
        pet = result.scalar_one_or_none()

        if not pet:
            return "❌ Питомец не найден или не на приключении."

        # Time Traveler skill: can always be recalled (but also can't be cancelled per wiki)
        # Per wiki: "Does not work on pets with the time traveler skill"
        if pet.skill == "time_traveler":
            return "❌ Питомец с Time Traveler не может быть отменён."

        pet.status = "idle"
        pet.adventure_type = None
        pet.adventure_started_at = None
        pet.adventure_ready_at = None
        await s.commit()

    return f"↩️ Питомец (ID: {pet_id}) возвращён с приключения."


async def pets_claim(user_id: int) -> str:
    """Claim adventure rewards. Rewards vary by adventure_type."""
    from database.engine import async_session
    from database.models import Pet, User
    from sqlalchemy import select

    data = _load()

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(
                Pet.user_id == user_id,
                Pet.status == "adventure",
                Pet.adventure_ready_at <= datetime.utcnow()
            )
        )
        pets = list(result.scalars().all())

        if not pets:
            return "❌ Нет питомцев с готовой наградой."

        # Fetch user for area context
        user = await s.get(User, user_id)
        area = user.area if user else 1

        all_rewards = {}
        messages = []

        for pet in pets:
            info = data["pets"].get(pet.pet_type, {})
            emoji = info.get("emoji", "🐾")
            name = info.get("name", pet.pet_type)
            adventure_type = pet.adventure_type or "find"

            # Check Time Traveler instant return
            instant_return = False
            if pet.skill == "time_traveler":
                rank_mult = PET_RANK_MULT.get(pet.skill_rank, 1)
                instant_chance = 0.10 * rank_mult / 9
                if random.random() < instant_chance:
                    instant_return = True

            # Check Ascended: chance to find new pet
            found_pet = False
            if pet.skill == "ascended":
                if random.random() < 0.15:
                    pet_result = await catch_pet(user_id, area)
                    if pet_result.get("caught"):
                        found_pet = True

            if adventure_type == "find":
                rewards = _claim_find(pet, data, area)
            elif adventure_type == "drill":
                rewards = _claim_drill(pet, data, area)
            elif adventure_type == "learn":
                rewards = _claim_learn(pet, data, s)
            else:
                rewards = _claim_find(pet, data, area)

            for mat, amt in rewards.items():
                all_rewards[mat] = all_rewards.get(mat, 0) + amt

            pet.status = "idle"
            pet.adventure_type = None
            pet.adventure_started_at = None
            pet.adventure_ready_at = None

            msg = f"{emoji} {name}: "
            if rewards:
                msg += ", ".join(f"+{a} {m}" for m, a in rewards.items())
            else:
                msg += "Ничего не найдено"
            if found_pet:
                msg += " | 🐾 Новый питомец!"
            messages.append(msg)

        await s.commit()

    # Give rewards
    if all_rewards:
        from database.crud import add_materials
        for mat, amt in all_rewards.items():
            if mat.startswith("coin:"):
                from game.player import add_coins
                await add_coins(user_id, amt)
            else:
                await add_materials(user_id, mat, amt)

    # Load material names for display
    with open(DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    names = mat_data.get("names", {})

    text = f"📦 <b>Награда с приключений!</b>\n\n"
    for msg in messages:
        text += msg + "\n"

    total = sum(all_rewards.values())
    text += f"\nВсего: {total} предметов"
    return text


def _claim_find(pet, data: dict, area: int) -> dict:
    """Rewards for find adventure — items."""
    adv = data["adventure"]["find"]
    score = pet.pet_score
    chance = adv["base_find_chance"] + score * adv["score_bonus_per_point"]
    max_finds = adv["max_finds"]

    # Lucky skill bonus
    lucky_bonus = 0
    if pet.skill == "lucky":
        lucky_bonus = adv.get("lucky_bonus", 0.15)

    finds = 0
    for _ in range(max_finds):
        if random.random() < min(chance, 0.95):
            finds += 1

    drops = {}
    for _ in range(finds):
        roll = random.random()
        if roll < 0.4 - lucky_bonus:
            mat = random.choice(["wooden_log", "normie_fish", "apple", "potato"])
            amt = random.randint(3, 15)
        elif roll < 0.7 - lucky_bonus * 0.5:
            mat = random.choice(["golden_fish", "epic_log", "banana", "wolfskin"])
            amt = random.randint(2, 8)
        elif roll < 0.85:
            mat = random.choice(["ruby", "unicornhorn", "zombieeye", "super_log"])
            amt = random.randint(1, 3)
        else:
            mat = random.choice(["mermaid_hair", "mega_log", "epic_fish", "unicornhorn"])
            amt = random.randint(1, 3)
        drops[mat] = drops.get(mat, 0) + amt

    return drops


def _claim_drill(pet, data: dict, area: int) -> dict:
    """Rewards for drill adventure — coins + items."""
    adv = data["adventure"]["drill"]
    score = pet.pet_score
    chance = adv["base_find_chance"] + score * adv["score_bonus_per_point"]
    max_finds = adv["max_finds"]

    # Digger skill bonus
    if pet.skill == "digger":
        chance += adv.get("digger_bonus", 0.20)

    finds = 0
    for _ in range(max_finds):
        if random.random() < min(chance, 0.95):
            finds += 1

    drops = {}
    for _ in range(finds):
        coin_amount = random.randint(50, 200) + score * 2
        drops["coin"] = drops.get("coin", 0) + coin_amount
        if random.random() < 0.3:
            mat = random.choice(["wooden_log", "normie_fish", "ruby", "apple"])
            drops[mat] = drops.get(mat, 0) + random.randint(1, 5)

    return drops


async def _claim_learn(pet, data: dict, session) -> dict:
    """Rewards for learn adventure — skill rank advance."""
    adv = data["adventure"]["learn"]
    skill_adv = data.get("skill_advance", {})
    base_chance = skill_adv.get("base_chance", 0.10)
    clever_bonus = adv.get("clever_bonus", 0.15)

    # Already at max rank?
    if pet.skill_rank == "SS+":
        return {"info": "уже максимальный ранг"}

    # Calculate advance chance
    chance = base_chance + pet.pet_score * adv.get("score_bonus_per_point", 0.01)
    if pet.skill == "clever":
        chance += clever_bonus

    # Less inputs = higher chance (simulated by score)
    chance = min(chance, 0.60)

    if random.random() < chance:
        new_rank = skill_rank_up(pet.skill_rank)
        if new_rank:
            pet.skill_rank = new_rank
            pet.pet_score = config.calc_pet_score(
                config.pet_tier_to_num(pet.pet_tier), pet.skill, new_rank
            )
            return {"rank_up": f"{pet.skill.title()} → [{new_rank}]"}

    return {}


# ────────────────────────────────────────────
# Fusion
# ────────────────────────────────────────────

async def pets_fusion(user_id: int, pet_ids: list[str]) -> str:
    """Fuse multiple pets. Higher tier result chance with more pets."""
    from database.engine import async_session
    from database.models import Pet, User
    from sqlalchemy import select

    data = _load()
    fusion_config = data["fusion"]

    async with async_session() as s:
        # Fetch all idle pets
        result = await s.execute(
            select(Pet).where(Pet.user_id == user_id, Pet.status == "idle").order_by(Pet.pet_score)
        )
        all_idle = {p.pet_id: p for p in result.scalars().all()}

        # Parse pet IDs
        if not pet_ids:
            # Auto-pick two lowest score
            sorted_idle = sorted(all_idle.values(), key=lambda p: p.pet_score)
            if len(sorted_idle) < 2:
                return "❌ Нужно минимум 2 питомца для слияния."
            selected = sorted_idle[:2]
        else:
            selected = []
            for pid_str in pet_ids:
                try:
                    pid = int(pid_str)
                    if pid in all_idle:
                        selected.append(all_idle[pid])
                except ValueError:
                    continue
            if len(selected) < 2:
                return "❌ Нужно минимум 2 свободных питомца."

        # Check max tier difference
        max_tier_diff = fusion_config.get("max_tier_diff_for_value", 5)
        tiers = [config.pet_tier_to_num(p.pet_tier) for p in selected]
        if max(tiers) - min(tiers) > max_tier_diff:
            return "❌ Слишком большая разница в тирах питомцев (макс. 5)."

        # Get user TT for boost
        user = await s.get(User, user_id)
        tt_count = user.tt_count if user else 0

        # Calculate total score
        total_score = sum(p.pet_score for p in selected)

        # Find best tier
        best_tier_num = max(config.pet_tier_to_num(p.pet_tier) for p in selected)

        # Calculate upgrade chance
        upgrade_chance = fusion_config["upgrade_chance_base"] + total_score * fusion_config["upgrade_chance_bonus_per_score"]
        upgrade_chance += tt_count * fusion_config.get("tt_boost_per_tt", 0.02)

        # Happy skill bonus
        for p in selected:
            if p.skill == "happy":
                upgrade_chance += fusion_config.get("happy_skill_bonus", 0.10)

        upgrade_chance = min(upgrade_chance, 0.85)

        # Result type: random from selected, or preserved event type
        result_type = random.choice([p.pet_type for p in selected])
        info = data["pets"].get(result_type, {})

        # Skill inheritance
        inherit_chance = fusion_config.get("skill_inherit_chance_base", 0.30)
        best_skill = "normie"
        best_rank = "F"
        for p in sorted(selected, key=lambda x: PET_SKILL_SCORES.get(x.skill, 0), reverse=True):
            if p.skill != "normie" and random.random() < inherit_chance:
                best_skill = p.skill
                best_rank = p.skill_rank
                break

        # Try tier upgrade
        current_roman = config.pet_num_to_tier(best_tier_num)
        upgraded = False

        if random.random() < upgrade_chance and best_tier_num < 25:
            best_tier_num += 1
            upgraded = True

        new_tier = config.pet_num_to_tier(best_tier_num)
        new_score = config.calc_pet_score(best_tier_num, best_skill, best_rank)

        # Delete all fused pets
        for p in selected:
            await s.delete(p)

        # Create new pet
        new_pet = Pet(
            user_id=user_id,
            pet_type=result_type,
            pet_tier=new_tier,
            pet_score=new_score,
            skill=best_skill,
            skill_rank=best_rank,
            pet_level=1,
            status="idle",
        )
        s.add(new_pet)
        await s.commit()

    emoji = info.get("emoji", "🐾")
    name = info.get("name", result_type)

    if upgraded:
        return (
            f"✨ <b>Слияние УСПЕШНО! Тир повышен!</b>\n\n"
            f"→ {emoji} <b>{name}</b> — Tier {new_tier}\n"
            f"Skill: {best_skill.title()} [{best_rank}]\n"
            f"Score: {new_score}"
        )
    else:
        return (
            f"❌ <b>Слияние — тир не повышен</b>\n\n"
            f"→ {emoji} <b>{name}</b> — Tier {new_tier}\n"
            f"Skill: {best_skill.title()} [{best_rank}]\n"
            f"Score: {new_score}\n"
            f"(Общий score +{total_score // 3} за счёт слияния)"
        )


async def pets_fusion_auto(user_id: int) -> str:
    """Auto-fuse all non-special idle pets without skills."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    data = _load()
    fusion_config = data["fusion"]

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(Pet.user_id == user_id, Pet.status == "idle").order_by(Pet.pet_score)
        )
        all_idle = list(result.scalars().all())

        # Filter: only normie-skill pets, not special types
        fuseable = [p for p in all_idle if p.skill == "normie"]

        if len(fuseable) < 2:
            return "❌ Нет питомцев для автослияния (нужны 2+ с навыком Normie)."

        fused_count = 0
        kept = []
        # Process in pairs
        i = 0
        while i < len(fuseable) - 1:
            p1 = fuseable[i]
            p2 = fuseable[i + 1]

            t1 = config.pet_tier_to_num(p1.pet_tier)
            t2 = config.pet_tier_to_num(p2.pet_tier)
            best_tier = max(t1, t2)
            total_score = p1.pet_score + p2.pet_score

            upgrade_chance = fusion_config["upgrade_chance_base"] + total_score * fusion_config["upgrade_chance_bonus_per_score"]
            upgrade_chance = min(upgrade_chance, 0.85)

            new_tier_num = best_tier
            if random.random() < upgrade_chance and best_tier < 25:
                new_tier_num = best_tier + 1

            new_tier = config.pet_num_to_tier(new_tier_num)
            new_score = config.calc_pet_score(new_tier_num, "normie", "F")
            result_type = random.choice([p1.pet_type, p2.pet_type])

            await s.delete(p1)
            await s.delete(p2)

            new_pet = Pet(
                user_id=user_id,
                pet_type=result_type,
                pet_tier=new_tier,
                pet_score=new_score,
                skill="normie",
                skill_rank="F",
                pet_level=1,
                status="idle",
            )
            s.add(new_pet)
            fused_count += 1
            i += 2

        await s.commit()

    return f"✨ Автослияние: {fused_count} операций выполнено."


# ────────────────────────────────────────────
# Tournament (kept as-is per user request)
# ────────────────────────────────────────────

async def pets_tournament(user_id: int) -> str:
    """Send a pet to tournament."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    data = _load()
    t_config = data["tournament"]

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(
                Pet.user_id == user_id,
                Pet.status == "idle",
                Pet.pet_score >= t_config["min_score_to_enter"]
            ).order_by(Pet.pet_score.desc())
        )
        best = result.scalar_one_or_none()

        if not best:
            return f"❌ Нет питомцев с Score >= {t_config['min_score_to_enter']} для турнира."

        best.status = "tournament"
        await s.commit()

    info = get_pet_info(best.pet_type)
    emoji = info["emoji"] if info else "🐾"
    return (
        f"🏆 <b>Турнир</b>\n\n"
        f"{emoji} {info['name'] if info else best.pet_type} (Tier {best.pet_tier}, Score {best.pet_score})\n"
        f"отправлен на турнир!\n"
        f"Результат будет известен через {t_config['duration_hours']}ч."
    )


# ────────────────────────────────────────────
# Release / Ascend
# ────────────────────────────────────────────

async def pets_release(user_id: int, pet_id: int) -> str:
    """Release a pet."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(Pet.user_id == user_id, Pet.pet_id == pet_id)
        )
        pet = result.scalar_one_or_none()

        if not pet:
            return "❌ Питомец не найден."

        if pet.status != "idle":
            return "❌ Нельзя выпустить питомца на приключении/турнире."

        info = get_pet_info(pet.pet_type)
        emoji = info["emoji"] if info else "🐾"
        name = info["name"] if info else pet.pet_type

        await s.delete(pet)
        await s.commit()

    return f"👋 {emoji} {name} (Tier {pet.pet_tier}, Score {pet.pet_score}) выпущен."


async def pets_ascend(user_id: int) -> str:
    """Ascend a pet — requires Tier III + high score."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select

    data = _load()
    asc_config = data["ascend"]

    async with async_session() as s:
        result = await s.execute(
            select(Pet).where(
                Pet.user_id == user_id,
                Pet.pet_tier == asc_config["required_tier"],
                Pet.pet_score >= asc_config["required_score"],
                Pet.status == "idle"
            )
        )
        pet = result.scalar_one_or_none()

        if not pet:
            return (
                f"❌ Нет питомцев для аскенции.\n"
                f"Требуется: Tier {asc_config['required_tier']}, Score >= {asc_config['required_score']}"
            )

        info = get_pet_info(pet.pet_type)
        emoji = info["emoji"] if info else "🐾"
        name = info["name"] if info else pet.pet_type

        # Master skill: higher tier pets on ascend
        extra_score = 20
        if pet.skill == "master":
            extra_score = 40

        pet.skill = asc_config["ascended_skill"]
        pet.skill_rank = "F"
        pet.pet_score += extra_score
        # Recalc with ascended skill
        pet.pet_score = config.calc_pet_score(
            config.pet_tier_to_num(pet.pet_tier), pet.skill, pet.skill_rank
        ) + extra_score
        await s.commit()

    return (
        f"🌟 <b>АСКЕНЦИЯ!</b>\n\n"
        f"{emoji} {name} получил навык: {asc_config['ascended_skill']}\n"
        f"Бонус: {asc_config['ascended_bonus']}\n"
        f"Score: {pet.pet_score}"
    )
