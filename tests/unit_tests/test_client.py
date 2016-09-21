"""
Test ``announcer.client`` (CLI).
"""
import logging
import sys

import pytest
import requests
from requests.exceptions import ConnectionError

from announcer import root_logger, root_logging_handler
from announcer.client import main
from announcer.exceptions import AnnouncerImproperlyConfigured
from announcer.service import Service


# This fixture needs to be located in this file
@pytest.fixture(autouse=True)
def fake_service(monkeypatch):
    """
    Disable all ``announcer.service.Service`` logic.

    :param monkeypatch: pytest "patching" fixture
    """
    monkeypatch.setattr(Service, '__init__', lambda *args, **kwargs: None)
    monkeypatch.setattr(Service, 'run', lambda self: None)


@pytest.mark.parametrize('command', [
    'consul-announcer',
    'consul-announcer --something --wrong -h',
    'consul-announcer --something --wrong --help'
], ids=['none', 'short', 'long'])
def test_client_help_message(command, monkeypatch, capfd):
    """
    Whenever you pass ``-h`` or ``--help`` - client should always show its help message.

    :param command: custom test function parameter: command to invoke
    :param monkeypatch: pytest "patching" fixture
    :param capfd: pytest fixture to capture command output
    """
    monkeypatch.setattr(sys, 'argv', command.split())
    with pytest.raises(SystemExit) as e:
        main()
    # Exit code is ``None`` which is normal termination code
    assert not e.value.code
    out, err = capfd.readouterr()
    # Check that help message was printed
    assert "Service announcer for Consul." in out


@pytest.mark.parametrize('command, mode', [
    ['consul-announcer --config=... -- ...', 'WEC'],
    ['consul-announcer --config=... -v -- ...', 'IWEC'],
    ['consul-announcer --config=... --verbose -- ...', 'IWEC'],
    ['consul-announcer --config=... -vv -- ...', 'DIWEC'],
    ['consul-announcer --config=... --verbose --verbose -- ...', 'DIWEC']
], ids=['none', 'lvl-1-short', 'lvl-1-long', 'lvl-2-short', 'lvl-2-long'])
def test_client_output_verbosity(command, mode, monkeypatch, capfd):
    """
    Test client output verbosity.

    :param command: custom test function parameter: command to invoke
    :param mode: custom test function parameter: logging mode (W - warning, E - error, etc)
    :param monkeypatch: pytest "patching" fixture
    :param capfd: pytest fixture to capture command output
    """
    monkeypatch.setattr(sys, 'argv', command.split())
    monkeypatch.setattr(root_logger, 'level', logging.DEBUG)
    monkeypatch.setattr(root_logging_handler, 'stream', sys.stdout)

    main()

    msg = {
        'D': "Test debug message",
        'I': "Test info message",
        'W': "Test warning message",
        'E': "Test error message",
        'C': "Test critical message"
    }

    # Any 'announcer.*' logger will use ``root_logging_handler``
    logger = logging.getLogger('announcer.tests')
    logger.debug(msg['D'])
    logger.info(msg['I'])
    logger.warning(msg['W'])
    logger.error(msg['E'])
    logger.critical(msg['C'])
    out, err = capfd.readouterr()

    for lvl in msg:
        if lvl in mode:
            assert msg[lvl] in out
        else:
            assert msg[lvl] not in out


@pytest.mark.parametrize('command, is_correct', [
    ['consul-announcer -- ...', False],
    ['consul-announcer --config=... -- ...', True]
], ids=['wrong', 'correct'])
def test_client_config_argument(command, is_correct, monkeypatch, capfd):
    """
    Test client's required argument: ``--config``.

    :param command: custom test function parameter: command to invoke
    :param is_correct: custom test function parameter: is the command correctly configured
    :param monkeypatch: pytest "patching" fixture
    :param capfd: pytest fixture to capture command output
    """
    monkeypatch.setattr(sys, 'argv', command.split())
    if is_correct:
        main()
        # No output expected - execution went fine
        assert capfd.readouterr() == ('', '')
    else:
        with pytest.raises(SystemExit) as e:
            main()
        # Exit code is 2 in case of misconfiguration
        assert e.value.code == 2
        out, err = capfd.readouterr()
        # Client misconfiguration error message
        assert "consul-announcer: error: {}".format(
            "argument --config is required" if sys.version < "3"
            else "the following arguments are required: --config"
        ) in err


@pytest.mark.parametrize('command, is_correct', [
    ['consul-announcer --config=...', False],
    ['consul-announcer --config=... -- ...', True]
], ids=['wrong', 'correct'])
def test_client_command_argument(command, is_correct, monkeypatch, capfd):
    """
    Test client's required argument: `` -- command [arguments]``.

    :param command: custom test function parameter: command to invoke
    :param is_correct: custom test function parameter: is the command correctly configured
    :param monkeypatch: pytest "patching" fixture
    :param capfd: pytest fixture to capture command output
    """
    monkeypatch.setattr(sys, 'argv', command.split())
    if is_correct:
        main()
        # No output expected - execution went fine
        assert capfd.readouterr() == ('', '')
    else:
        with pytest.raises(SystemExit) as e:
            main()
        # Exit code is 2 in case of misconfiguration
        assert e.value.code == 2
        out, err = capfd.readouterr()
        # Client misconfiguration error message
        assert "consul-announcer: error: command is not specified" in err


@pytest.mark.parametrize('exception', [
    AnnouncerImproperlyConfigured("Fake test error"),
    ConnectionError(request=requests.Request(url='http://fake.example.com'))
], ids=['service', 'connection'])
def test_client_error(exception, monkeypatch, capfd):
    def fake_service_init(*args, **kwargs):
        raise exception

    monkeypatch.setattr(sys, 'argv', 'consul-announcer --config=... -- ...'.split())
    monkeypatch.setattr(root_logging_handler, 'stream', sys.stdout)
    monkeypatch.setattr(Service, '__init__', fake_service_init)

    with pytest.raises(SystemExit) as e:
        main()

    # Exit code is 1 in case of service error
    assert e.value.code == 1
    out, err = capfd.readouterr()
    # Client misconfiguration error message
    if isinstance(exception, ConnectionError):
        error_message = "Can't connect to \"{}\"".format(exception.request.url)
    else:
        error_message = str(exception)
    assert "ERROR - announcer.client: {}".format(error_message) in out
