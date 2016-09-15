import pytest

from doorkeeper.service import Service


@pytest.fixture
def fake_consul(monkeypatch):
    """
    Disable ``doorkeeper.service.Service`` calls to Consul API.

    :param monkeypatch: pytest "patching" fixture
    """
    monkeypatch.setattr(Service, 'register_services', lambda self: None)
    monkeypatch.setattr(Service, 'pass_ttl_check', lambda self, check_id: True)
    monkeypatch.setattr(Service, 'deregister_services', lambda self: None)


@pytest.fixture
def fake_subprocess(monkeypatch):
    """
    Disable ``doorkeeper.service.Service`` subprocess spawning & polling.

    :param monkeypatch: pytest "patching" fixture
    """
    monkeypatch.setattr(Service, 'invoke_process', lambda self, *args, **kwargs: None)
    monkeypatch.setattr(Service, 'poll', lambda self: None)


@pytest.fixture
def fake_service(fake_consul, fake_subprocess):
    """
    Disable all external interactions of  ``doorkeeper.service.Service``.

    :param fake_consul: custom fixture to disable calls to Consul API
    :param fake_subprocess: custom fixture to disable subprocess spawning
    """
    pass
