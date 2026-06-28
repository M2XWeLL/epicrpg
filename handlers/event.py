"""Event button callback handler — edits the event message to show participant count."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from game.events import handle_event_click, active_events, EVENT_TYPES, EVENT_WINDOW

router = Router()


@router.callback_query(F.data.startswith("event:"))
async def cb_event(callback: CallbackQuery):
    event_type = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    result = await handle_event_click(chat_id, event_type, user_id)
    if result["success"]:
        await callback.answer(result["message"], show_alert=False)
    else:
        await callback.answer(result["message"], show_alert=True)

    # Edit the original event message to show live participant count
    key = f"{chat_id}_{event_type}"
    event = active_events.get(key)
    if event and event.get("message_id"):
        info = EVENT_TYPES.get(event_type, {})
        count = len(event["clicks"])
        try:
            await callback.message.edit_text(
                f"🌍 <b>{info.get('label', event_type)}!</b>\n"
                f"Участников: {count} | Минимум: 3\n"
                f"Нажмите кнопку чтобы участвовать!",
                reply_markup=callback.message.reply_markup,
                parse_mode="HTML",
            )
        except Exception:
            pass  # Message may be too old to edit
