import json
import logging
import signal
import subprocess
import time

import consul
from consul.base import CB
from requests.structures import CaseInsensitiveDict

from doorkeeper.exceptions import DoorkeeperImproperlyConfigured
from doorkeeper.utils import parse_duration

logger = logging.getLogger(__name__)


class Service(object):
    consul = None
    process = None
    config = None
    services = None
    ttl_checks = None
    interval = None

    def __init__(self, agent_address, config, cmd, interval=1):
        """
        Initialize a Doorkeeper service.

        :param str agent_address: Agent address in a form: "hostname:port" (port is optional)
        :param config: Config file path
        :param str cmd: Command to invoke, e.g.: "uwsgi --init=...". It should run in foreground.
        :param float interval: Polling interval in seconds.
                               May be ``None`` so it will be auto-calculated as min TTL / 10.
        """
        logger.info("Initializing Doorkeeper service")
        self.consul = consul.Consul(*agent_address.split(':', 1))
        self.parse_services(config)
        self.parse_interval(interval)
        self.register_services()
        self.invoke_process(cmd)
        self.poll()
        self.deregister_services()

    def invoke_process(self, cmd):
        """
        Invoke the sub-process to monitor.

        :param str cmd:
        """
        logger.info("Starting process: {}".format(cmd))
        self.process = subprocess.Popen(cmd.split())
        self.handle_signals()

    def handle_signals(self):
        """
        Transparently pass all the incoming signals to the invoked process.
        """
        for i in dir(signal):
            if i.startswith("SIG") and '_' not in i:
                signum = getattr(signal, i)
                try:
                    signal.signal(signum, self.handle_signal)
                except (RuntimeError, OSError, ValueError):
                    # Some signals cannot be catched and will raise errors:
                    # RuntimeException on SIGKILL and OSError on SIGSTOP.
                    # No signals can be catched inside threads - ValueError will be raised.
                    pass

    def handle_signal(self, signal_number, *args):
        """
        OS signal listener that passes the signal to the invoked process.

        :param int signal_number:
        :param args:
        """
        self.process.send_signal(signal_number)

    def parse_services(self, config):
        """
        Parse Consul services config.

        See https://www.consul.io/docs/agent/services.html
        and https://www.consul.io/docs/agent/checks.html.

        :param str config: Config file path
        :raises: DoorkeeperValidationError
        """
        logger.info("Parsing services definition in \"{}\" config file".format(config))

        self.services = {}
        self.ttl_checks = {}

        with open(config) as f:
            self.config = json.load(f, object_hook=CaseInsensitiveDict)

        if 'service' in self.config:
            self.parse_service(self.config['service'])

        if 'services' in self.config:
            if not isinstance(self.config['services'], list):
                raise DoorkeeperImproperlyConfigured(
                    "\"services\" must be an array in {}".format(self.config)
                )
            for service in self.config['services']:
                self.parse_service(service)

        if not self.services:
            raise DoorkeeperImproperlyConfigured(
                "Please specify either \"service\" config or non-empty \"services\" list"
            )

    def parse_service(self, service):
        """
        Parse Consul service config.

        Simple validation:

        - "name" is required
        - "id" is "name", if not specified
        - "id" should be unique

        Service config is stored in ``self.services``.
        TTL checks detected and stored in ``self.ttl_checks``.

        :param dict service: Service config
        :raises: DoorkeeperValidationError
        """
        if 'name' not in service:
            raise DoorkeeperImproperlyConfigured(
                "\"name\" is missing in {}".format(service)
            )

        service_id = service.get('id', service['name'])

        if service_id in self.services:
            raise DoorkeeperImproperlyConfigured(
                "Service ID \"{}\" is duplicated".format(service_id)
            )

        self.services[service_id] = service

        if 'check' in service and 'ttl' in service['check']:
            self.ttl_checks['service:{}'.format(service_id)] = service['check']

        if 'checks' in service:
            if not isinstance(service['checks'], list):
                raise DoorkeeperImproperlyConfigured(
                    "\"checks\" must be an array in {}".format(service)
                )
            for i, check in enumerate(service['checks'], 1):
                if 'ttl' in check:
                    self.ttl_checks['service:{}:{}'.format(service_id, i)] = check

    def parse_interval(self, interval):
        """
        Process polling interval.

        - If it's ``None`` - calculate it as min TTL / 10
        - If it's not ``None`` and it's greater than min TTL - log a warning

        :param float interval:
        :raises: DoorkeeperValidationError
        """
        logger.info("Processing the polling interval")

        self.interval = interval
        min_ttl = self.get_min_ttl()
        logger.debug("Min TTL is {}".format(
            '{} sec'.format(min_ttl) if min_ttl is not None else 'not available'
        ))

        if min_ttl is not None:
            if interval is None:
                self.interval = min_ttl / 10
                logger.debug("Polling interval is auto calculated as min TTL / 10 = {} sec".format(
                    self.interval
                ))
            elif interval > min_ttl:
                logger.warning(
                    "Polling interval ({} sec) is greater than min TTL ({} sec)".format(
                        interval, min_ttl
                    )
                )
        elif interval is None:
            raise DoorkeeperImproperlyConfigured("Polling interval is undefined")

    def get_min_ttl(self):
        """
        Find the minimum TTL value among all TTL checks.
        :return: TTL value in seconds
        :rtype: float
        """
        min_ttl = None
        for check in self.ttl_checks.values():
            ttl = parse_duration(check['ttl']).total_seconds()
            if min_ttl is None or ttl < min_ttl:
                min_ttl = ttl
        return min_ttl

    def register_services(self):
        """
        Register services in Consul agent.
        """
        logger.info("Registering Consul services")
        for service_id, service_conf in self.services.items():
            logger.debug("Registering service \"{}\": {}".format(service_id, service_conf))
            # Use low-level ``self.consul.http`` instead of ``self.consul.agent.service.register``
            # because we don't want to parse the service config - we just pass it as-is.
            success = self.consul.http.put(
                CB.bool(),
                '/v1/agent/service/register',
                data=json.dumps(service_conf, default=dict)
            )
            if not success:
                logger.warning("Service \"{}\" was not registered".format(service_id))

    def deregister_services(self):
        """
        Deregister services in Consul agent.
        """
        logger.info("Deregistering Consul services")
        for service_id in self.services:
            logger.debug("Deregistering service \"{}\"".format(service_id))
            success = self.consul.agent.service.deregister(service_id)
            if not success:
                logger.warning("Service \"{}\" was not deregistered".format(service_id))

    def poll(self):
        """
        Check if invoked process is still running and mark all related TTL checks as passed.
        """
        logger.info("Start polling the process with PID {} every {} sec".format(
            self.process.pid, self.interval
        ))

        while True:
            time.sleep(self.interval)
            if self.process.poll() is None:
                self.pass_ttl_checks()
            else:
                break

    def pass_ttl_checks(self):
        """
        Mark all the registered TTL checks as passed.
        """
        if self.ttl_checks:
            statuses = []
            for check_id in self.ttl_checks:
                success = self.consul.agent.check.ttl_pass(check_id)
                statuses.append('\"{}\" - {}'.format(check_id, 'passed' if success else 'failed'))
            logger.debug("Updating TTL checks: {}".format(', '.join(statuses)))
        else:
            logger.debug("No TTL checks registered")

    def __del__(self):
        """
        Cleanup on object destruction.
        """
        if self.process and self.process.poll() is None:
            logger.info("Killing the process {} (cleanup)".format(self.process.pid))
            self.process.kill()
