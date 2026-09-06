from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import main_menu
from bot.keyboards.reply import phone_buttons
from bot.services.api_client import api
from bot.states import LinkState

router = Router()


def normalize_phone(raw: str) -> str:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits.startswith("8"):
        digits = "9" + digits[1:]
    if not digits.startswith("998"):
        digits = "998" + digits
    return "+" + digits[:12]


def role_menu_text(role):
    titles = {
        "student": "🎓 O'quvchi menyusi",
        "teacher": "👨‍🏫 O'qituvchi menyusi",
        "admin": "🛡 Administrator menyusi",
    }
    return titles.get(role, "Menyu")


@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    status, data = await api.whoami(message.from_user.id)
    if status == 200:
        await message.answer(
            f"Xush kelibsiz, {data['full_name']}! 👋\n\n{role_menu_text(data['role'])}",
            reply_markup=main_menu(data["role"]),
        )
        return

    await message.answer(
        "Salom! Sizni tanimadim. 📱 Telefon raqamingizni yuboring.\n"
        "Raqam tizimda +998XXXXXXXXX ko'rinishida saqlangan bo'lishi kerak.",
        reply_markup=phone_buttons(),
    )


@router.message(F.contact)
async def phone_received(message: types.Message, state: FSMContext):
    phone = normalize_phone(message.contact.phone_number)
    telegram_id = message.from_user.id

    status, data = await api.link(phone, telegram_id)
    if status == 200:
        await state.set_state(LinkState.waiting_code)
        await state.update_data(phone=phone, telegram_id=telegram_id, code=data.get("code"))
        await message.answer(
            f"Telefon raqam topildi: {phone}\n\n"
            "Tasdiqlash kodi o'qituvchi/administratorga bildiriladi. "
            f"Kodni kiriting (masalan: {data.get('code')}):",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return
    if status == 404:
        await message.answer(
            "❌ Bu raqam tizimda yo'q. Administratorga murojaat qiling.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return

    await message.answer("🛑 Server javob bermayapti, birozdan keyin urinib ko'ring.")


@router.message(LinkState.waiting_code, F.text)
async def code_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = message.text.strip()

    status, data = await api.link_with_code(data["phone"], data["telegram_id"], code)
    if status == 200:
        await state.clear()
        role = data.get("role")
        user = data.get("user", {})
        await message.answer(
            f"✅ Akkaunt bog'landi. Xush kelibsiz, {user.get('full_name', '')}!\n\n"
            f"{role_menu_text(role)}",
            reply_markup=main_menu(role),
        )
        return

    detail = data.get("detail", "Kod noto'g'ri.")
    if "3 marta" in detail or "muddati" in detail:
        await state.clear()
        await message.answer(f"❌ {detail}\nQaytadan /start bosing.")
        return

    await message.answer(f"❌ {detail}")


@router.callback_query(F.data == "back_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    status, data = await api.whoami(callback.from_user.id)
    if status == 200:
        await callback.message.edit_text(
            f"{role_menu_text(data['role'])}",
            reply_markup=main_menu(data["role"]),
        )
    else:
        await callback.message.answer("Iltimos, /start bosing.")


@router.callback_query(F.data == "cancel")
async def cancel_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Bekor qilindi. ❌")
    await back_to_menu(callback, state)


@router.callback_query(F.data == "noop")
async def noop(callback: types.CallbackQuery):
    await callback.answer()