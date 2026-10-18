from aiogram.filters import Filter
from aiogram.types import Message

class IsModerator(Filter):
    def __init__(self, moderator_ids: list[int]):
        self.moderator_ids = moderator_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.moderator_ids