from contextvars import ContextVar #用于创建 线程/协程隔离的 上下文变量

current_itcode: ContextVar[str | None] = ContextVar("current_usercode", default=None)
