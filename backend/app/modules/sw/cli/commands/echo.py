from ..registry import register_command


def handler(args):
    # Simply return the text provided
    return args.get('text', '')


register_command('echo', handler, description='Echo text back', args_schema={'text': 'str'})
