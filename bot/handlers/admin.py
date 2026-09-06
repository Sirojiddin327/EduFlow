from aiogram import F, Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.inline import debtors_group_buttons
from bot.services.api_client import api
from bot.utils.formatters import format_debt_message, format_debtors, format_payment_list

router = Router()

PAGE_SIZE = 20


async def _whoami_or_none(telegram_id):
    status, data = await api.whoami(telegram_id)
    if status != 200:
        return None
    return data


async def _check_admin(callback: types.CallbackQuery):
    me = await _whoami_or_none(callback.from_user.id)
    if not me or me["role"] != "admin":
        return None
    return me


def _debtor_keyboard(debtors, group_id, page, total_pages):
    builder = InlineKeyboardBuilder()
    for d in debtors:
        builder.button(
            text=f"👤 {d['full_name']} — {d['debt']} so'm",
            callback_data=f"debtor_detail:{d['student_id']}",
        )
    nav = []
    if page > 1:
        nav.append(builder.button(text="◀️", callback_data=f"debtors:{group_id}:{page-1}"))
    nav.append(builder.button(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(builder.button(text="▶️", callback_data=f"debtors:{group_id}:{page+1}"))
    builder.button(
        text="🔄 Yangilash", callback_data=f"debtors:{group_id}:{page}"
    )
    builder.button(text="◀️ Orqaga", callback_data="back_menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data.startswith("debtors:"))
async def show_debtors(callback: types.CallbackQuery):
    me = await _check_admin(callback)
    if not me:
        return await callback.answer(
            "Bu bo'lim faqat administrator uchun", show_alert=True
        )

    _, group_id, page_str = callback.data.split(":")
    page = int(page_str)
    group_id = None if group_id == "all" else int(group_id)

    if group_id is None:
        status, data = await api.groups()
        if status != 200:
            return await callback.message.answer("🛑 Server javob bermayapti.")
        groups = data.get("results") if isinstance(data, dict) else []
        active = [g for g in groups if g.get("is_active")]
        return await callback.message.edit_text(
            "Guruhni tanlang:", reply_markup=debtors_group_buttons(active)
        )

    status, data = await api.debtors(group_id=group_id, page=1, page_size=100)
    if status != 200:
        return await callback.message.answer("🛑 Server javob bermayapti.")

    debtors = data.get("debtors", [])
    total_pages = max(1, (len(debtors) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, total_pages)
    chunk = debtors[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    group_name = chunk[0]["group_name"] if chunk else f"Guruh #{group_id}"
    title = f"🔴 Qarzdorlar — {group_name}"
    text = format_debtors(
        {"debtors": chunk, "total_debt": data.get("total_debt", 0)}, title
    )

    await callback.message.edit_text(
        text, reply_markup=_debtor_keyboard(chunk, group_id, page, total_pages)
    )


@router.callback_query(F.data.startswith("debtor_detail:"))
async def debtor_detail(callback: types.CallbackQuery):
    me = await _check_admin(callback)
    if not me:
        return await callback.answer(
            "Bu bo'lim faqat administrator uchun", show_alert=True
        )

    student_id = int(callback.data.split(":")[1])
    status, data = await api.student_debt(student_id)
    if status != 200:
        return await callback.message.answer("🛑 Ma'lumot olinmadi.")

    text = format_debt_message(data)

    status, pays = await api.my_payments(student_id)
    if status == 200:
        results = pays.get("results") if isinstance(pays, dict) else []
        text += "\n\n" + format_payment_list(results[:5])

    await callback.message.edit_text(text)