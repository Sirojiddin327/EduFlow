from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(role):
    buttons = []
    if role == "student":
        buttons = [
            [InlineKeyboardButton(text="💰 Mening qarzim", callback_data="my_debt")],
            [InlineKeyboardButton(text="📅 Mening davomatim", callback_data="my_attendance")],
        ]
    elif role == "teacher":
        buttons = [
            [InlineKeyboardButton(text="✅ Davomat belgilash", callback_data="mark_attendance")],
        ]
    elif role == "admin":
        buttons = [
            [InlineKeyboardButton(text="📊 Qarzdorlar", callback_data="debtors:all:1")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def debt_actions():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧾 To'lovlar tarixi", callback_data="my_payments"),
            ],
            [
                InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_menu"),
            ],
        ]
    )


def back_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_menu")]]
    )


def attendance_log_buttons():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Oxirgi 10 dars", callback_data="attendance_log"),
            ],
            [
                InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_menu"),
            ],
        ]
    )


def group_buttons(groups, action="att_group"):
    rows = [
        [InlineKeyboardButton(text=g["name"], callback_data=f"{action}:{g['id']}")]
        for g in groups
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def debtors_group_buttons(groups):
    rows = [
        [InlineKeyboardButton(text="🌐 Hamma guruhlar", callback_data="debtors:all:1")]
    ]
    rows += [
        [InlineKeyboardButton(text=g["name"], callback_data=f"debtors:{g['id']}:1")]
        for g in groups
    ]
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def date_buttons():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Bugun", callback_data="att_date:today"),
                InlineKeyboardButton(text="📅 Kecha", callback_data="att_date:yesterday"),
            ],
            [
                InlineKeyboardButton(text="✏️ Boshqa sana", callback_data="att_date:other"),
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
            ],
        ]
    )


def marking_buttons(marks):
    status_icons = {"": "⬜", "present": "✅", "absent": "❌", "late": "🕐", "excused": "📄"}
    rows = []
    for student_id, mark in marks.items():
        icon = status_icons.get(mark.get("status", ""), "⬜")
        name = mark.get("name", "")
        rows.append(
            [InlineKeyboardButton(text=f"{icon} {name}", callback_data=f"att_toggle:{student_id}")]
        )
    rows.append(
        [InlineKeyboardButton(text="✅ Hammasi keldi", callback_data="att_all")],
    )
    rows.append(
        [InlineKeyboardButton(text="💾 Saqlash", callback_data="att_save")],
    )
    rows.append(
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_save():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_no"),
            ],
        ]
    )


def debtors_pagination(total_pages, group_id, page):
    rows = []
    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(text="◀️", callback_data=f"debtors:{group_id}:{page-1}")
        )
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(text="▶️", callback_data=f"debtors:{group_id}:{page+1}")
        )
    rows.append(nav)
    rows.append(
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"debtors:{group_id}:{page}")]
    )
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)