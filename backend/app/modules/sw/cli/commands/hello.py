from ..registry import register_command


def handler(args, context=None):
    # context is expected to be the user dict returned by get_current_user
    user = None
    try:
        if isinstance(context, dict):
            user = context.get('sub') or context.get('user') or context.get('username')
    except Exception:
        user = None

    if not user:
        user = 'guest'

    return f"Hello {user}. How are you today?"


register_command('hello', handler, description='Greet the logged in user', args_schema={})
