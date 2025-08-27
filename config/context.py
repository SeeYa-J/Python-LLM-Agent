from contextvars import ContextVar

current_itcode: ContextVar[str | None] = ContextVar("current_usercode", default=None)
