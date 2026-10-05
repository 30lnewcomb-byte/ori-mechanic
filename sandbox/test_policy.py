from sandbox.policy import validate_command

def test_allows_python():
    assert validate_command("python -c 'print(123)'")[0]

def test_rejects_shell_escape():
    assert not validate_command("bash -c 'echo nope'")[0]

def test_rejects_network_tools():
    assert not validate_command("curl https://example.com")[0]

def test_rejects_privileged_actions():
    assert not validate_command("sudo reboot")[0]
