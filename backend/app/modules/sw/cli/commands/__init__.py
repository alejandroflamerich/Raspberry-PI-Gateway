from ..registry import register_command

# Commands can alternatively auto-register by importing modules here
try:
    from . import echo  # noqa: F401
    from . import health  # noqa: F401
    from . import hello  # noqa: F401
    from . import getvar  # noqa: F401
    from . import last_req  # noqa: F401
    from . import pollers  # noqa: F401
except Exception:
    # best-effort import; tests or environment may not execute submodule imports
    pass
