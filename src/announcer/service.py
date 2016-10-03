import json
import logging
import signal
import subprocess
import time

import consul
from consul.base import CB
from requests.structures import CaseInsensitiveDict

from announcer.exceptions import AnnouncerImproperlyConfigured
from announcer.utils import parse_duration

logger = logging.getLogger(__name__)


class Service(object):
    consul = None
    cmd = None
    config = None
    interval = None
    process = None
    services = None
    ttl_checks = None

    def __init__(self, agent_address, config, cmd, token=None, interval=1):
        """
        Initialize consul-announcer service.

        :param str agent_address: Agent address in a form: "hostname:port" (port is optional).
        :param config: Consul configuration JSON. If starts with @ - considered as file path.
        :param list cmd: Command to invoke in , e.g.: ['uwsgi', '--ini=...']". No daemons allowed.
        :param token: Consul ACL token.
        :type token: str or None
        :param interval: Polling interval in seconds. If None - auto-calculated as min TTL / 10.
        :type interval: float or None
        """
        logger.info("Initializing service")
        self.consul = consul.Consul(*agent_address.split(':', 1), token=token)
        self.cmd = cmd
        self.parse_services(config)
        self.parse_interval(interval)

    def run(self):
        """
        Run the service:

        - register services & checks in Consul
        - invoke a subprocess
        - poll it (keep it alive in Consul)
        - deregister services after subprocess is finished
        """
        try:
            self.register_services()
            self.invoke_process()
            self.poll()
        finally:
            self.deregister_services()

    def parse_services(self, config):
        """
        Parse Consul services config.

        See https://www.consul.io/docs/agent/services.html
        and https://www.consul.io/docs/agent/checks.html.

        :param str config: Consul configuration JSON. If starts with @ - considered as file path.
        :raises: AnnouncerValidationError
        """
        self.services = {}
        self.ttl_checks = {}

        if config[0] == '@':
            logger.info("Parsing services definition in \"{}\" config file".format(config[1:]))
            with open(config[1:]) as f:
                self.config = json.load(f, object_hook=CaseInsensitiveDict)
        else:
            logger.info("Parsing services definition: {}".format(config))
            self.config = json.loads(config, object_hook=CaseInsensitiveDict)

        if 'service' in self.config:
            self.parse_service(self.config['service'])

        if 'services' in self.config:
            if not isinstance(self.config['services'], list):
                raise AnnouncerImproperlyConfigured(
                    "\"services\" must be an array in {}".format(self.config)
                )

            for service_conf in self.config['services']:
                self.parse_service(service_conf)

        if not self.services:
            raise AnnouncerImproperlyConfigured(
                "Please specify either \"service\" config or non-empty \"services\" list"
            )

    def parse_service(self, service_conf):
        """
        Parse Consul service config.

        Simple validation:

        - "name" is required
        - "id" is "name", if not specified
        - "id" should be unique

        Service config is stored in ``self.services``.

        :param dict service_conf: Service config
        :raises: AnnouncerValidationError
        """
        if 'name' not in service_conf:
            raise AnnouncerImproperlyConfigured(
                "\"name\" is missing in {}".format(service_conf)
            )

        service_id = service_conf.get('id', service_conf['name'])

        if service_id in self.services:
            raise AnnouncerImproperlyConfigured(
                "Service ID \"{}\" is duplicated".format(service_id)
            )

        self.services[service_id] = service_conf

        if 'check' in service_conf:
            self.parse_check(service_conf['check'], 'service:{}'.format(service_id))

        if 'checks' in service_conf:
            if not isinstance(service_conf['checks'], list):
                raise AnnouncerImproperlyConfigured(
                    "\"checks\" must be an array in {}".format(service_conf)
                )

            for i, check_conf in enumerate(service_conf['checks'], 1):
                self.parse_check(check_conf, 'service:{}:{}'.format(service_id, i))

    def parse_check(self, check_conf, check_id):
        """
        Parse Consul check config.

        No validation. TTL checks are detected & stored in ``self.ttl_checks``.

        :param dict check_conf: Check config
        :param str check_id: When check is inside service, its Name & ID are auto-generated
                             from service Name & ID
        """
        if 'ttl' in check_conf:
            self.ttl_checks[check_id] = check_conf

    def parse_interval(self, interval):
        """
        Process polling interval.

        - If it's ``None`` - calculate it as min TTL / 10
        - If it's not ``None`` and it's greater than min TTL - log a warning

        :param float interval:
        :raises: AnnouncerValidationError
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
            raise AnnouncerImproperlyConfigured("Polling interval is undefined")

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
                params={'token': self.consul.token},
                data=json.dumps(service_conf, default=dict)
            )
            if not success:
                logger.warning("Service \"{}\" was not registered".format(service_id))

    def invoke_process(self):
        """
        Invoke the sub-process to monitor.
        """
        logger.info("Starting process: {}".format(' '.join(self.cmd)))
        self.process = subprocess.Popen(self.cmd)
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
                success = self.pass_ttl_check(check_id)
                statuses.append('\"{}\" - {}'.format(check_id, 'passed' if success else 'failed'))
            logger.debug("Updating TTL checks: {}".format(', '.join(statuses)))
        else:
            logger.debug("No TTL checks registered")

    def pass_ttl_check(self, check_id):
        """
        Mark specified TTL check as passed.

        :param str check_id:
        """
        return self.consul.agent.check.ttl_pass(check_id)

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

    def __del__(self):
        """
        Cleanup on object destruction.
        """
        if self.process and self.process.poll() is None:
            logger.info("Killing the process {} (cleanup)".format(self.process.pid))
            self.process.kill()
