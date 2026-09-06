from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bot_api.models import BotLinkCode
from apps.bot_api.serializers import BotLinkSerializer, BotWhoamiSerializer
from apps.users.models import User
from config.authentication import IsBotToken


class BotLinkView(APIView):
    authentication_classes = []
    permission_classes = [IsBotToken]

    def post(self, request):
        serializer = BotLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        telegram_id = serializer.validated_data["telegram_id"]
        code = serializer.validated_data.get("code", "")

        try:
            user = User.objects.get(phone=phone, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"detail": "Bu raqam tizimda yo'q. Administratorga murojaat qiling."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if User.objects.filter(telegram_id=telegram_id).exclude(pk=user.pk).exists():
            return Response(
                {"detail": "Bu telegram akkaunt boshqa foydalanuvchiga bog'langan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not code:
            link = BotLinkCode.generate_for(user)
            return Response(
                {
                    "detail": "Tasdiqlash kodi yuborildi.",
                    "code": link.code,
                },
                status=status.HTTP_200_OK,
            )

        link = getattr(user, "link_code", None)
        if link is None or link.is_expired:
            return Response(
                {"detail": "Kod muddati tugagan. /start bosib qaytadan urinib ko'ring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if link.attempts >= 3:
            return Response(
                {"detail": "3 marta xato kiritdingiz. /start bosib qaytadan urinib ko'ring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if link.code != code:
            link.attempts += 1
            link.save(update_fields=["attempts"])
            remaining = 3 - link.attempts
            return Response(
                {"detail": f"Kod noto'g'ri. {remaining} ta urinish qoldi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.telegram_id = telegram_id
        user.save(update_fields=["telegram_id"])
        link.delete()

        return Response(
            {
                "detail": "Akkaunt bog'landi.",
                "user": BotWhoamiSerializer(user).data,
                "role": user.role,
            },
            status=status.HTTP_200_OK,
        )


class BotWhoamiView(APIView):
    authentication_classes = []
    permission_classes = [IsBotToken]

    def get(self, request):
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            return Response(
                {"detail": "telegram_id parametri kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Akkaunt bog'lanmagan."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(BotWhoamiSerializer(user).data)