import json
import random
import config
from database.crud import add_profession_xp, get_profession_bonus

# Crafter XP per equipment tier (wiki)
CRAFTER_EQUIP_XP = {
    1: 4,    # Wooden sword/armor
    2: 6,    # Fish sword/armor
    4: 8,    # Apple sword / Eye armor
    6: 10,   # Zombie sword / Banana armor
    8: 12,   # Ruby sword / Epic armor
    11: 14,  # Unicorn sword / Ruby armor
    14: 16,  # Hair sword / Coin armor
    17: 18,  # Coin sword / Mermaid armor
    20: 20,  # Electronical sword/armor
    50: 22,  # EDGY sword/armor
    70: 50,  # ULTRA-EDGY (forge)
    100: 75, # OMEGA (forge)
    200: 100, # ULTRA-OMEGA (forge)
}


def load_recipes() -> dict:
    path = config.DATA_DIR / "recipes.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_craft_cost(tier: int) -> dict | None:
    recipes = load_recipes()
    craft = recipes.get("craft", {})
    return craft.get(str(tier))


def get_recipe_info(tier: int) -> str:
    cost = get_craft_cost(tier)
    if not cost:
        return "❌ Рецепт не найден."

    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    mat_names = mat_data.get("names", {})

    msg = f"⚒️ Крафт Тир {cost['level']}\n\n"
    msg += f"⚔️ {cost['weapon_name']} ({cost['weapon_atk']} ATK)\n"
    for mat, amt in cost.get("weapon_materials", {}).items():
        name = mat_names.get(mat, mat)
        msg += f"  • {name} × {amt}\n"
    msg += f"\n🛡️ {cost['armor_name']} ({cost['armor_def']} DEF)\n"
    for mat, amt in cost.get("armor_materials", {}).items():
        name = mat_names.get(mat, mat)
        msg += f"  • {name} × {amt}\n"
    return msg


async def craft_equipment(user_id: int, tier: int) -> dict:
    """Craft weapon+armor at given tier."""
    from database.crud import get_user, get_equipment, has_materials, remove_materials, set_equipment

    user = await get_user(user_id)
    eq = await get_equipment(user_id)
    if not user or not eq:
        return {"success": False, "message": "Игрок не найден."}

    cost = get_craft_cost(tier)
    if not cost:
        return {"success": False, "message": "❌ Рецепт не найден."}

    if user.level < cost["level"]:
        return {"success": False, "message": f"❌ Нужен уровень {cost['level']} для этого рецепта."}

    # Check weapon materials
    weapon_mats = cost.get("weapon_materials", {})
    if not await has_materials(user_id, weapon_mats):
        return {"success": False, "message": "❌ Недостаточно ресурсов для оружия."}

    # Check armor materials
    armor_mats = cost.get("armor_materials", {})
    if not await has_materials(user_id, armor_mats):
        return {"success": False, "message": "❌ Недостаточно ресурсов для брони."}

    # Execute
    for mat, amt in weapon_mats.items():
        await remove_materials(user_id, mat, amt)
    for mat, amt in armor_mats.items():
        await remove_materials(user_id, mat, amt)

    # Crafter profession: chance to save materials (wiki: 12.25% base, scales with level)
    from database.crud import add_materials as _add_mats
    bonuses = await get_profession_bonus(user_id, "crafter")
    save_chance = bonuses.get("save_recipe_chance", 0)
    saved = {}
    if save_chance > 0:
        all_mats = {}
        for mat, amt in weapon_mats.items():
            all_mats[mat] = all_mats.get(mat, 0) + amt
        for mat, amt in armor_mats.items():
            all_mats[mat] = all_mats.get(mat, 0) + amt
        for mat, total_amt in all_mats.items():
            if random.random() < save_chance:
                save_amt = max(1, int(total_amt * 0.1225))
                await _add_mats(user_id, mat, save_amt)
                saved[mat] = save_amt

    new_eq = {"weapon_tier": tier, "armor_tier": tier}
    await set_equipment(user_id, new_eq)

    crafter_xp = CRAFTER_EQUIP_XP.get(tier, 10)
    await add_profession_xp(user_id, "crafter", crafter_xp)

    msg = f"✅ Скрафчено!\n⚔️ {cost['weapon_name']} ({cost['weapon_atk']} ATK)\n🛡️ {cost['armor_name']} ({cost['armor_def']} DEF)"
    if saved:
        saved_text = ", ".join(f"{amt}x {m}" for m, amt in saved.items())
        msg += f"\n🎉 Crafter бонус: сохранено {saved_text}"

    # Quest hook
    from game.quest import on_craft
    first_mat = next(iter(all_mats.keys()), "crafted_item")
    await on_craft(user_id, first_mat, 1)

    return {"success": True, "message": msg}


async def dismantle_equipment(user_id: int) -> dict:
    """Dismantle current equipment. Returns 80% of materials used to craft it."""
    from database.crud import get_equipment, get_user, add_materials, set_equipment

    eq = await get_equipment(user_id)
    user = await get_user(user_id)
    if not user or not eq:
        return {"success": False, "message": "Игрок не найден."}

    tier = eq.get("weapon_tier", 1)
    if tier <= 1:
        return {"success": False, "message": "❌ Нельзя разобрать Тир 1 снаряжение."}

    recipes = load_recipes()

    # Find the recipe: check forge first (level 70+), then craft recipes
    recipe = recipes.get("forge", {}).get(str(tier))
    if not recipe:
        recipe = recipes.get("craft", {}).get(str(tier))

    if not recipe:
        return {"success": False, "message": "❌ Рецепт не найден."}

    # Return 80% of ALL materials from weapon + armor recipes
    returned = {}
    for source in ("weapon_materials", "armor_materials"):
        for mat, amt in recipe.get(source, {}).items():
            # Don't return base items (previous tier sword/armor used in forging)
            if mat.endswith("_sword") or mat.endswith("_armor"):
                continue
            return_amt = max(1, int(amt * 0.8))
            returned[mat] = returned.get(mat, 0) + return_amt

    for mat, amt in returned.items():
        await add_materials(user_id, mat, amt)

    # Downgrade equipment
    new_eq = {"weapon_tier": tier - 1, "armor_tier": tier - 1}
    await set_equipment(user_id, new_eq)

    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    mat_names = mat_data.get("names", {})

    mat_text = " + ".join(f"{amt}x {mat_names.get(m, m)}" for m, amt in returned.items())

    # Crafter XP for dismantling (same as crafting)
    crafter_xp = CRAFTER_EQUIP_XP.get(tier, 10)
    await add_profession_xp(user_id, "crafter", crafter_xp)

    return {
        "success": True,
        "message": f"🔧 Разобрано! Возвращено (80%): {mat_text}\n⬇️ Снаряжение → Тир {tier-1}"
    }
