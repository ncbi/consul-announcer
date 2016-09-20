"""
Test ``announcer.service.Service`` interaction with subprocess and Consul (faked).
"""
import json
import logging
import time

import responses

from announcer import root_logger
from announcer.service import Service


def test_subprocess_alive(fake_consul):
    """
    Test ``announcer.service.Service`` subprocess spawning.

    :param fake_consul: custom fixture to disable calls to Consul API
    """
    service = Service('localhost', 'tests/config/correct.json', ['sleep', '0.5'], 0.2)
    service.poll = lambda: None
    service.run()
    assert service.process.poll() is None
    time.sleep(1)
    assert service.process.poll() == 0


def test_subprocess_polling(fake_consul, caplog, monkeypatch):
    """
    Test ``announcer.service.Service`` subprocess keeping alive.

    :param fake_consul: custom fixture to disable calls to Consul API
    :param caplog: ``pytest-catchlog`` fixture to catch Python logs
    :param monkeypatch: pytest "patching" fixture
    """
    monkeypatch.setattr(root_logger, 'level', logging.DEBUG)
    service = Service('localhost', 'tests/config/correct.json', ['sleep', '0.2'], 0.1)
    service.run()
    assert service.process.poll() == 0

    # No TTL checks - log a message
    service = Service('localhost', 'tests/config/correct-no-ttl.json', ['sleep', '0.2'], 0.1)
    service.run()
    assert service.process.poll() == 0
    assert caplog.records[-1].message == "No TTL checks registered"


def test_subprocess_cleanup(fake_consul):
    """
    Test ``announcer.service.Service`` subprocess termination when Python process has exited.

    :param fake_consul: custom fixture to disable calls to Consul API
    """
    service = Service('localhost', 'tests/config/correct.json', ['tail', '-f', '/dev/null'])
    service.poll = lambda: None
    service.run()
    service.__del__()  # this method is called by Python on garbage collection
    time.sleep(0.5)  # we need to wait some time until the process is killed
    assert service.process.poll() is not None  # subprocess was killed


@responses.activate
def test_consul_interaction():
    """
    Test ``announcer.service.Service`` interaction with Consul.
    """
    api_url = 'http://localhost:1234/v1/agent/{}'

    def request_callback(request):
        service_conf = json.loads(request.body)
        return 408 if service_conf.get('Id') == 'service-2' else 200, {}, ''

    # Empty 200 response for successful service register
    responses.add_callback(
        responses.PUT, api_url.format('service/register'), callback=request_callback
    )

    # Empty 200 response for successful service deregister
    responses.add(responses.GET, api_url.format('service/deregister/Service%201'))
    responses.add(responses.GET, api_url.format('service/deregister/service-1.1'))

    # Empty 200 response for successful check pass
    responses.add(responses.GET, api_url.format('check/pass/service:service-2:2'))

    # HTTP 404 while deregisternig this service
    responses.add(responses.GET, api_url.format('service/deregister/service-2'), status=404)

    Service('localhost:1234', 'tests/config/correct.json', ['sleep', '0.2'], 0.1).run()
