from app.modules.sw.cli import registry


def test_list_commands_contains_echo_and_health():
    cmds = registry.list_commands()
    names = {c['name'] for c in cmds}
    assert 'echo' in names
    assert 'health' in names


def test_execute_echo():
    res = registry.execute('echo', {'text': 'hello'})
    assert res['ok'] is True
    assert 'hello' in res['output']
