from aiogram import F, Router, types

from bot.keyboards.inline import (
    attendance_log_buttons,
    back_button,
    debt_actions,
    main_menu,
)
from bot.services.api_client import api
from bot.utils.formatters import (
    format_attendance_log,
    format_attendance_summary,
    format_debt_message,
    format_payment_list,
)

router = Router()


async def _whoami_or_none(telegram_id):
    status, data = await api.whoami(telegram_id)
    if status != 200:
        return None
    return data


@router.callback_query(F.data == "my_debt")
async def my_debt(callback: types.CallbackQuery):
    me = await _whoami_or_none(callback.from_user.id)
    if not me or me["role"] != "student":
        return await callback.answer("Bu bo'lim faqat o'quvchilar uchun", show_alert=True)

    status, data = await api.student_debt(me["id"])
    if status != 200:
        return await callback.message.answer("🛑 Server javob bermayapti, birozdan keyin urinib ko'ring.")
    await callback.message.edit_text(
        format_debt_message(data), reply_markup=debt_actions()
    )


@router.callback_query(F.data == "my_payments")
async def my_payments(callback: types.CallbackQuery):
    me = await _whoami_or_none(callback.from_user.id)
    if not me or me["role"] != "student":
        return await callback.answer("Bu bo'lim faqat o'quvchilar uchun", show_alert=True)

    status, data = await api.my_payments(me["id"])
    if status != 200:
        return await callback.message.answer("🛑 Server javob bermayapti, birozdan keyin urinib ko'ring.")
    payments = data.get("results") if isinstance(data, dict) else []
    await callback.message.edit_text(
        format_payment_list(payments), reply_markup=debt_actions()
    )


@router.callback_query(F.data == "my_attendance")
async def my_attendance(callback: types.CallbackQuery):
    me = await _whoami_or_none(callback.from_user.id)
    if not me or me["role"] != "student":
        return await callback.answer("Bu bo'lim faqat o'quvchilar uchun", show_alert=True)

    status, data = await api.attendance_summary(me["id"])
    if status != 200:
        return await callback.message.answer("🛑 Server javob bermayapti, birozdan keyin urinib ko'ring.")
    await callback.message.edit_text(
        format_attendance_summary(data), reply_markup=attendance_log_buttons()
    )


@router.callback_query(F.data == "attendance_log")
async def attendance_log(callback: types.CallbackQuery):
    me = await _whoami_or_none(callback.from_user.id)
    if not me or me["role"] != "student":
        return await callback.answer("Bu bo'lim faqat o'quvchilar uchun", show_alert=True)

    status, data = await api.my_attendance(me["id"])
    if status != 200:
        return await callback.message.answer("🛑 Server javob bermayapti, birozdan keyin urinib ko'ring.")
    rows = data.get("results") if isinstance(data, dict) else []
    await callback.message.edit_text(
        format_attendance_log(rows), reply_markup=back_button()
    )