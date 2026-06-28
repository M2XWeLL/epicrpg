"""
Professions commands: /professions, /profession [profession], /profession claim, /profession rewards.
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, get_profession
from game.professions import (
    format_professions, format_profession_detail, PROFESSIONS,
    claim_profession_reward, claim_all_rewards, MILESTONES, ascend,
)

router = Router()


@router.message(F.text == "/professions")
async def cmd_professions(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    prof_data = await get_profession(message.from_user.id)
    if not prof_data:
        prof_data = {
            "worker_level": 1, "worker_xp": 0,
            "crafter_level": 1, "crafter_xp": 0,
            "lootboxer_level": 1, "lootboxer_xp": 0,
            "merchant_level": 1, "merchant_xp": 0,
            "enchanter_level": 1, "enchanter_xp": 0,
            "claimed": "{}",
        }

    text = format_professions(prof_data)
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/profession rewards")
async def cmd_profession_rewards(message: Message):
    text = "🎁 <b>Profession rewards</b>\n\n"
    for ms, data in sorted(MILESTONES.items()):
        text += f"Level {ms} rewards: {data['desc']}\n"
    text += "\nUse profession rewards claim to claim the pending rewards!"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/profession rewards claim")
@router.message(F.text == "/profession claim")
async def cmd_profession_claim(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    result = await claim_all_rewards(message.from_user.id)
    await message.answer(result, parse_mode="HTML")


@router.message(F.text == "/profession")
@router.message(F.text.startswith("/profession "))
async def cmd_profession(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if not args:
        await message.answer(
            "Используйте: /profession [worker/crafter/lootboxer/merchant/enchanter]"
        )
        return

    prof_data = await get_profession(message.from_user.id)
    if not prof_data:
        prof_data = {
            "worker_level": 1, "worker_xp": 0,
            "crafter_level": 1, "crafter_xp": 0,
            "lootboxer_level": 1, "lootboxer_xp": 0,
            "merchant_level": 1, "merchant_xp": 0,
            "enchanter_level": 1, "enchanter_xp": 0,
            "claimed": "{}",
        }

    prof_key = args[0].lower()
    if prof_key not in PROFESSIONS:
        await message.answer("❌ Профессия не найдена. Доступные: " + ", ".join(PROFESSIONS.keys()))
        return

    text = format_profession_detail(prof_key, prof_data)
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/professions ascend")
@router.message(F.text == "/pr ascend")
async def cmd_professions_ascend(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if user.ascended:
        await message.answer("❌ Вы уже вознесены.")
        return

    result = await ascend(message.from_user.id)
    await message.answer(result["message"], parse_mode="HTML")
