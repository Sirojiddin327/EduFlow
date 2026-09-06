import aiohttp

from bot.config import API_BASE_URL, BOT_API_TOKEN


class APIClient:

    def __init__(self):
        self.base = API_BASE_URL
        self.headers = {"X-Bot-Token": BOT_API_TOKEN}

    async def _request(self, method, path, params=None, json=None):
        url = self.base + path
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(
                headers=self.headers, timeout=timeout
            ) as session:
                async with session.request(method, url, params=params, json=json) as resp:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        data = {}
                    return resp.status, data
        except (aiohttp.ClientError, OSError):
            return None, {}

    async def get(self, path, params=None):
        return await self._request("GET", path, params=params)

    async def post(self, path, json=None):
        return await self._request("POST", path, json=json)

    async def whoami(self, telegram_id):
        return await self.get("/api/bot/whoami/", {"telegram_id": telegram_id})

    async def link(self, phone, telegram_id):
        return await self.post("/api/bot/link/", {"phone": phone, "telegram_id": telegram_id})

    async def link_with_code(self, phone, telegram_id, code):
        return await self.post(
            "/api/bot/link/",
            {"phone": phone, "telegram_id": telegram_id, "code": code},
        )

    async def groups(self):
        return await self.get("/api/groups/")

    async def find_lesson(self, group_id, date):
        return await self.get("/api/lessons/", {"group": group_id, "date": date})

    async def create_lesson(self, group_id, date, topic):
        return await self.post(
            "/api/lessons/", {"group": group_id, "date": date, "topic": topic}
        )

    async def lesson_attendance(self, lesson_id):
        return await self.get(f"/api/lessons/{lesson_id}/attendance/")

    async def save_attendance(self, lesson_id, marks):
        return await self.post(f"/api/lessons/{lesson_id}/attendance/", json=marks)

    async def student_debt(self, student_id):
        return await self.get(f"/api/reports/student-debt/{student_id}/")

    async def my_payments(self, student_id):
        return await self.get(
            "/api/payments/", {"enrollment__student": student_id, "page_size": 10}
        )

    async def attendance_summary(self, student_id):
        return await self.get(
            "/api/reports/attendance-summary/", {"student": student_id}
        )

    async def my_attendance(self, student_id):
        return await self.get(
            "/api/attendance/", {"student": student_id, "page_size": 10}
        )

    async def debtors(self, group_id=None, page=1, page_size=20):
        params = {"min_debt": 1, "page": page, "page_size": page_size}
        if group_id:
            params["group"] = group_id
        return await self.get("/api/reports/debtors/", params)


api = APIClient()