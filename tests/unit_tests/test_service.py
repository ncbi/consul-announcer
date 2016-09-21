"""
Test ``announcer.service.Service`` (without CLI).
"""
import pytest

from announcer.exceptions import AnnouncerImproperlyConfigured
from announcer.service import Service


@pytest.mark.parametrize('conf_path', [
    'tests/config/wrong.json',
    'tests/config/wrong-services-key.json',
    'tests/config/no-services.json',
    'tests/config/service-without-name.json',
    'tests/config/service-id-duplicate.json',
    'tests/config/wrong-checks-key.json'
], ids=[
    'wrong JSON',
    'wrong "services" key',
    'no services',
    'service without "name"',
    'service ID duplicate',
    'wrong "checks" key'
])
def test_services_config_parsing_errors(conf_path):
    """
    Test ``announcer.service.Service`` initialization - Consul config parsing errors.
    """
    with pytest.raises(AnnouncerImproperlyConfigured):
        Service('localhost', conf_path, ['...'])


def test_services_config_parsing_success(fake_service):
    """
    Test ``announcer.service.Service`` initialization - Consul config parsing success.

    :param fake_service: custom fixture to disable calls to Consul API and  subprocess spawning
    """
    service = Service('localhost', 'tests/config/correct.json', ['...'])
    assert len(service.services) == 3
    assert len(service.ttl_checks) == 1


def test_interval_parsing(fake_service, caplog):
    """
    Test ``announcer.service.Service`` initialization - interval parsing.
    """
    # Interval is provided
    assert Service('localhost', 'tests/config/correct.json', ['...'], 3).interval == 3

    # Default interval is 1 sec
    assert Service('localhost', 'tests/config/correct.json', ['...']).interval == 1

    # Interval is auto-calculated as min TTL / 10
    assert Service('localhost', 'tests/config/correct.json', ['...'], None).interval == 1.5

    # No TTL specified
    with pytest.raises(AnnouncerImproperlyConfigured):
        Service('localhost', 'tests/config/correct-no-ttl.json', ['...'], None)

    Service('localhost', 'tests/config/correct.json', ['...'], 20.0)
    log_record = caplog.records[-1]
    assert log_record.levelname == 'WARNING'
    assert log_record.message == 'Polling interval (20.0 sec) is greater than min TTL (15.0 sec)'
