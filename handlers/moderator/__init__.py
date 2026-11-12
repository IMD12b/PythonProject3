# handlers/moderator/__init__.py
from handlers.moderator.applications import mod_applications_router
from handlers.moderator.couriers import mod_couriers_router
from handlers.moderator.dispatchers import mod_dispatchers_router
from handlers.moderator.shifts import mod_shifts_router
from handlers.moderator.stats import mod_stats_router

__all__ = [
    "mod_applications_router",
    "mod_couriers_router",
    "mod_dispatchers_router",
    "mod_shifts_router",
    "mod_stats_router"
]