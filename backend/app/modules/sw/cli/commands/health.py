from ..registry import register_command
import time


_start = time.time()


def handler(args):
    return {
        'uptime_seconds': time.time() - _start,
        'status': 'ok',
    }


register_command('health', handler, description='Service health', args_schema={})
