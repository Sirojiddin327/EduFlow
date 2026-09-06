ATTENDANCE_STATUS = {
    "present": "✅ keldi",
    "absent": "❌ kelmadi",
    "late": "🕐 kechikdi",
    "excused": "📄 sababli",
}

PAYMENT_METHOD = {
    "cash": "💵 Naqd",
    "card": "💳 Karta",
    "transfer": "🔁 O'tkazma",
}


def format_money(value):
    """500000.00 -> '500 000 so'm'"""
    try:
        num = int(float(value))
    except (TypeError, ValueError):
        return "0 so'm"
    return f"{num:n}".replace(",", " ") + " so'm"


def format_debt_message(data):
    """O'quvchining guruhlar kesimidagi qarzi haqidagi matn."""
    lines = [f"👤 {data.get('full_name', '')}"]
    total = 0
    for e in data.get("enrollments", []):
        debt = e.get("debt")
        try:
            debt = float(debt)
        except (TypeError, ValueError):
            debt = 0
        total += debt
        lines.append("")
        lines.append(f"📚 {e['group_name']}")
        lines.append(f"Oylik: {format_money(e['monthly_price'])}")
        lines.append(
            f"Hisoblangan: {e['months']} oy × {format_money(e['monthly_price'])} "
            f"= {format_money(e['expected'])}"
        )
        lines.append(f"To'langan: {format_money(e['paid'])}")
        if debt <= 0:
            lines.append("🟢 Qarzingiz yo'q. Rahmat!")
            if debt < 0:
                lines.append(f"(Oldindan {format_money(-debt)} to'langansiz)")
        else:
            lines.append(f"🔴 Qarz: {format_money(debt)}")
    total_debt = data.get("total_debt", total)
    lines.append("")
    lines.append(f"Jami qarz: {format_money(total_debt)}")
    return "\n".join(lines)


def format_payment_list(payments):
    if not payments:
        return "To'lovlar topilmadi."
    lines = ["🧾 To'lovlar tarixi:"]
    for p in payments[:10]:
        lines.append(
            f"🗓 {p['period']} uchun — {format_money(p['amount'])}"
            f" ({PAYMENT_METHOD.get(p['method'], p['method'])})"
        )
    return "\n".join(lines)


def format_attendance_summary(rows):
    if not rows:
        return "Hozircha davomat ma'lumoti yo'q."
    lines = []
    for r in rows:
        lines.append(
            f"📚 {r['group_name']}: {r['held_lessons']} darsdan "
            f"{r['present'] + r['late']} tasida bo'ldingiz ({r['percent']}%)"
        )
        lines.append(
            f"✅ {r['present']} · ❌ {r['absent']} · 🕐 {r['late']} · 📄 {r['excused']}"
        )
        if r["percent"] < 70:
            lines.append("⚠️ Davomatingiz past. Darslarni qoldirmang!")
        lines.append("")
    return "\n".join(lines).strip()


def format_attendance_log(rows):
    if not rows:
        return "Oxirgi darslar bo'yicha ma'lumot yo'q."
    lines = ["📋 Oxirgi 10 dars:"]
    for a in rows:
        lines.append(
            f"{a.get('lesson_date', '')} — {a.get('lesson_topic', '')} — "
            f"{ATTENDANCE_STATUS.get(a.get('status'), a.get('status'))}"
        )
    return "\n".join(lines)


def format_debtors(data, title):
    debtors = data.get("debtors", [])
    if not debtors:
        return f"{title}\n\nHech qanday qarzdor yo'q. 🎉"
    lines = [f"{title} ({len(debtors)} ta, jami {format_money(data.get('total_debt', 0))})"]
    for i, d in enumerate(debtors, start=1):
        lines.append(f"{i}. {d['full_name']} — {format_money(d['debt'])} ({d['phone']})")
    return "\n".join(lines)