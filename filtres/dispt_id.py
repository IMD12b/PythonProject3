from aiogram.filters import Filter
from aiogram.types import Message

class IsAdmin(Filter):
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        # Проверяем, есть ли ID пользователя в переданном списке
        return message.from_user.id in self.admin_ids