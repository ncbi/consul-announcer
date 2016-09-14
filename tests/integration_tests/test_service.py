"""
Test ``doorkeeper.service.Service`` (without CLI).
"""
import pytest
from doorkeeper.exceptions import DoorkeeperImproperlyConfigured

from doorkeeper.service import Service


@pytest.fixture
def fake_service_subprocess(monkeypatch):
    """
    Disable ``doorkeeper.service.Service.invoke_process(cmd)``
    and ``doorkeeper.service.Service.poll()``.

    :param monkeypatch: pytest "patching" fixture
    """
    monkeypatch.setattr(Service, 'invoke_process', lambda *args, **kwargs: None)


@pytest.mark.parametrize('conf_path', [
    'tests/config/wrong.json'
], ids=['wrong JSON'])
def test_service_config_parsing(conf_path):
    """
    Test ``doorkeeper.service.Service`` initialization - Consul config parsing.
    """
    with pytest.raises(DoorkeeperImproperlyConfigured):
        Service('localhost', conf_path, '...')
