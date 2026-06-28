from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.crud import get_cooldowns
from utils.formatters import format_cooldowns
from utils.keyboards import cooldowns_keyboard

router = Router()


@router.message(F.text == "/cooldowns")
@router.message(F.text == "/cd")
@router.message(F.text == "/rd")
async def cmd_cooldowns(message: Message):
    cd = await get_cooldowns(message.from_user.id)
    cd_data = {
        "hunt_last": cd.hunt_last,
        "adventure_last": cd.adventure_last,
        "chop_last": cd.chop_last,
        "mine_last": cd.mine_last,
        "fish_last": cd.fish_last,
        "last_farm": cd.last_farm,
    }
    text = format_cooldowns(message.from_user.id, cd_data)
    await message.answer(text, parse_mode="HTML", reply_markup=cooldowns_keyboard())


@router.callback_query(F.data == "cooldowns:refresh")
async def cb_cooldowns_refresh(callback: CallbackQuery):
    cd = await get_cooldowns(callback.from_user.id)
    cd_data = {
        "hunt_last": cd.hunt_last,
        "adventure_last": cd.adventure_last,
        "chop_last": cd.chop_last,
        "mine_last": cd.mine_last,
        "fish_last": cd.fish_last,
        "last_farm": cd.last_farm,
    }
    text = format_cooldowns(callback.from_user.id, cd_data)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cooldowns_keyboard())
    await callback.answer("Обновлено!")
