from datetime import date, timedelta

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import (
    confirm_save,
    date_buttons,
    group_buttons,
    main_menu,
    marking_buttons,
)
from bot.services.api_client import api
from bot.states import AttendanceState
from bot.utils.statuses import STATUS_CYCLE

router = Router()


async def _whoami_or_none(telegram_id):
    status, data = await api.whoami(telegram_id)
    if status != 200:
        return None
    return data


@router.callback_query(F.data == "mark_attendance")
async def start_marking(callback: types.CallbackQuery, state: FSMContext):
    me = await _whoami_or_none(callback.from_user.id)
    if not me or me["role"] != "teacher":
        return await callback.answer("Bu bo'lim faqat o'qituvchi uchun", show_alert=True)

    status, data = await api.groups()
    groups = data.get("results") if isinstance(data, dict) else []
    active_groups = [g for g in groups if g.get("is_active")]
    if not active_groups:
        return await callback.message.edit_text("Sizga biriktirilgan faol guruh yo'q.")

    await state.set_state(AttendanceState.group)
    await callback.message.edit_text(
        "Guruhni tanlang:", reply_markup=group_buttons(active_groups, "att_group")
    )


@router.callback_query(AttendanceState.group, F.data.startswith("att_group:"))
async def group_selected(callback: types.CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])
    await state.update_data(group_id=group_id)
    await state.set_state(AttendanceState.date)
    await callback.message.edit_text("Dars sanasini tanlang:", reply_markup=date_buttons())


@router.callback_query(AttendanceState.date, F.data.startswith("att_date:"))
async def date_selected(callback: types.CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    if value == "today":
        d = date.today()
    elif value == "yesterday":
        d = date.today() - timedelta(days=1)
    else:
        await state.set_state(AttendanceState.date)
        await callback.message.edit_text("Sanani KK.OO.YYYY ko'rinishida yuboring:")
        return

    await state.update_data(date=d.isoformat())
    await state.set_state(AttendanceState.topic)
    await callback.message.edit_text("Dars mavzusini yozing:")


@router.message(AttendanceState.date, F.text)
async def custom_date(message: types.Message, state: FSMContext):
    try:
        d = date(*map(int, reversed(message.text.strip().split("."))))
    except (ValueError, TypeError):
        return await message.answer("Sana noto'g'ri. KK.OO.YYYY formatida yozing:")
    await state.update_data(date=d.isoformat())
    await state.set_state(AttendanceState.topic)
    await message.answer("Dars mavzusini yozing:")


@router.message(AttendanceState.topic, F.text)
async def topic_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    group_id = data["group_id"]
    date_iso = data["date"]

    status, found = await api.find_lesson(group_id, date_iso)
    lesson = None
    if status == 200:
        results = found.get("results") if isinstance(found, dict) else []
        for l in results:
            if l.get("date") == date_iso:
                lesson = l
                break

    if not lesson:
        status, created = await api.create_lesson(group_id, date_iso, message.text.strip())
        if status != 201:
            return await message.answer("🛑 Dars yaratib bo'lmadi. Qaytadan urinib ko'ring.")
        lesson = created

    await state.update_data(lesson_id=lesson["id"])

    status, sheet = await api.lesson_attendance(lesson["id"])
    if status != 200:
        return await message.answer("🛑 Davomat varaqasini olib bo'lmadi.")

    marks = {}
    for i, item in enumerate(sheet, start=1):
        marks[item["student"]] = {"name": f"{i}. {item.get('student_full_name', '')}", "status": ""}

    await state.update_data(marks=marks)
    await state.set_state(AttendanceState.marking)
    await message.answer("Davomatni belgilang:", reply_markup=marking_buttons(marks))


@router.callback_query(AttendanceState.marking, F.data.startswith("att_toggle:"))
async def toggle_student(callback: types.CallbackQuery, state: FSMContext):
    student_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    marks = data.get("marks", {})

    current = marks.get(student_id, {}).get("status", "")
    next_idx = (STATUS_CYCLE.index(current) + 1) if current in STATUS_CYCLE else 0
    marks[student_id]["status"] = STATUS_CYCLE[next_idx]

    await state.update_data(marks=marks)
    await callback.message.edit_reply_markup(reply_markup=marking_buttons(marks))


@router.callback_query(AttendanceState.marking, F.data == "att_all")
async def mark_all(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    marks = data.get("marks", {})
    for m in marks.values():
        m["status"] = "present"
    await state.update_data(marks=marks)
    await callback.message.edit_reply_markup(reply_markup=marking_buttons(marks))


@router.callback_query(AttendanceState.marking, F.data == "att_save")
async def save_attendance(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    marks = data.get("marks", {})
    unmarked = [sid for sid, m in marks.items() if not m.get("status")]

    if unmarked:
        await state.update_data(confirm=True)
        return await callback.message.edit_text(
            f"{len(unmarked)} ta o'quvchi belgilanmadi. Baribir saqlaymizmi?",
            reply_markup=confirm_save(),
        )

    await _do_save(callback, state)


@router.callback_query(F.data == "confirm_yes")
async def confirm_save(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Saqlanmoqda...")
    await _do_save(callback, state)


@router.callback_query(F.data == "confirm_no")
async def confirm_no(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(
        "Davomatni davom ettiring:", reply_markup=marking_buttons(data.get("marks", {}))
    )


async def _do_save(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lesson_id = data.get("lesson_id")
    marks = data.get("marks", {})

    payload = [
        {
            "student": sid,
            "status": m["status"],
            "comment": "",
        }
        for sid, m in marks.items()
        if m.get("status")
    ]

    status, resp = await api.save_attendance(lesson_id, payload)
    if status != 200:
        return await callback.message.answer(
            "🛑 Saqlashda xatolik. Birozdan keyin urinib ko'ring."
        )

    counts = {}
    for m in payload:
        counts[m["status"]] = counts.get(m["status"], 0) + 1

    parts = []
    order = {"present": "keldi", "late": "kechikdi", "absent": "kelmadi", "excused": "sababli"}
    for st, label in order.items():
        if counts.get(st):
            parts.append(f"{counts[st]} {label}")

    await state.clear()
    me = await _whoami_or_none(callback.from_user.id)
    await callback.message.answer(
        f"✅ Saqlandi: {', '.join(parts)}" if parts else "✅ Saqlandi.",
        reply_markup=main_menu(me["role"]) if me else None,
    )