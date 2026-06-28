"""
Pets commands: /pets info, detail, summary, adventure (find/learn/drill/cancel),
claim, fusion (multi + auto), tournament, release, ascend.
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user
from game.pets import (
    pets_info, pets_detail, pets_summary, pets_adventure, pets_adventure_cancel,
    pets_claim, pets_fusion, pets_fusion_auto, pets_tournament,
    pets_release, pets_ascend,
)

router = Router()


@router.message(F.text == "/pets")
@router.message(F.text.startswith("/pets "))
async def cmd_pets(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:]

    if not args or args[0] == "info":
        text = await pets_info(message.from_user.id)
        await message.answer(text, parse_mode="HTML")
        return

    sub = args[0].lower()

    if sub == "detail":
        if len(args) < 2:
            await message.answer("Формат: /pets detail [pet_id]")
            return
        try:
            pet_id = int(args[1])
        except ValueError:
            await message.answer("❌ Введите ID питомца (число).")
            return
        text = await pets_detail(message.from_user.id, pet_id)
        await message.answer(text, parse_mode="HTML")
        return

    if sub == "summary":
        text = await pets_summary(message.from_user.id)
        await message.answer(text, parse_mode="HTML")
        return

    if sub == "adventure":
        if len(args) < 2 or args[1].lower() == "info":
            text = (
                "⚔️ <b>Pet Adventure</b>\n\n"
                "3 типа приключений:\n"
                "  /pets adventure find [ids] — поиск предметов\n"
                "  /pets adventure learn [ids] — прокачка навыков\n"
                "  /pets adventure drill [ids] — добыча монет\n\n"
                "Отмена: /pets adventure cancel [id]"
            )
            await message.answer(text, parse_mode="HTML")
            return

        adv_type = args[1].lower()

        if adv_type == "cancel":
            if len(args) < 3:
                await message.answer("Формат: /pets adventure cancel [pet_id]")
                return
            try:
                pet_id = int(args[2])
            except ValueError:
                await message.answer("❌ Введите ID питомца.")
                return
            text = await pets_adventure_cancel(message.from_user.id, pet_id)
            await message.answer(text, parse_mode="HTML")
            return

        if adv_type not in ("find", "learn", "drill"):
            await message.answer("❌ Тип: find, learn или drill.")
            return

        pet_ids = args[2:] if len(args) > 2 else []
        text = await pets_adventure(message.from_user.id, adv_type, pet_ids)
        await message.answer(text, parse_mode="HTML")
        return

    if sub == "claim":
        text = await pets_claim(message.from_user.id)
        await message.answer(text, parse_mode="HTML")
        return

    if sub == "fusion":
        if len(args) > 1 and args[1].lower() == "automatic":
            text = await pets_fusion_auto(message.from_user.id)
            await message.answer(text, parse_mode="HTML")
            return

        pet_ids = args[1:] if len(args) > 1 else []
        text = await pets_fusion(message.from_user.id, pet_ids)
        await message.answer(text, parse_mode="HTML")
        return

    if sub == "tournament":
        text = await pets_tournament(message.from_user.id)
        await message.answer(text, parse_mode="HTML")
        return

    if sub == "release":
        if len(args) < 2:
            await message.answer("Формат: /pets release [pet_id]")
            return
        try:
            pet_id = int(args[1])
        except ValueError:
            await message.answer("❌ Введите ID питомца.")
            return
        text = await pets_release(message.from_user.id, pet_id)
        await message.answer(text, parse_mode="HTML")
        return

    if sub == "ascend":
        text = await pets_ascend(message.from_user.id)
        await message.answer(text, parse_mode="HTML")
        return

    await message.answer(
        "🐾 <b>Команды питомцев:</b>\n\n"
        "/pets info — Информация\n"
        "/pets detail [id] — Детали питомца\n"
        "/pets summary — Сводка\n"
        "/pets adventure find/learn/drill [ids] — Приключение\n"
        "/pets adventure cancel [id] — Отменить приключение\n"
        "/pets claim — Получить награду\n"
        "/pets fusion [ids] — Слияние\n"
        "/pets fusion automatic — Автослияние\n"
        "/pets release [id] — Выпустить\n"
        "/pets ascend — Аскенция\n"
        "/pets tournament — Турнир",
        parse_mode="HTML"
    )
