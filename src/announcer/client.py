import argparse
import logging
import os
import sys

from requests.exceptions import ConnectionError

from announcer import root_logger
from announcer.exceptions import AnnouncerImproperlyConfigured
from announcer.service import Service


logger = logging.getLogger(__name__)


class ArgsFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        """
        Add '-- command [arguments]' to usage.
        """
        actions.append(argparse._StoreAction(option_strings=[], dest="-- command [arguments]"))
        return super(ArgsFormatter, self).add_usage(usage, actions, groups, prefix)


def main():
    parser = argparse.ArgumentParser(
        'consul-announcer',
        description="Service announcer for Consul.",
        formatter_class=ArgsFormatter
    )

    parser.add_argument(
        '--agent',
        default=os.getenv('CONSUL_ANNOUNCER_AGENT', 'localhost'),
        help="Consul agent address: hostname[:port]. "
             "Default: localhost (default port is 8500). "
             "You can also use CONSUL_ANNOUNCER_AGENT env variable.",
        metavar='hostname[:port]'
    )

    parser.add_argument(
        '--config',
        required='CONSUL_ANNOUNCER_CONFIG' not in os.environ,
        default=os.getenv('CONSUL_ANNOUNCER_CONFIG'),
        help="Consul configuration JSON (required). "
             "If starts with @ - considered as file path. "
             "You can also use CONSUL_ANNOUNCER_CONFIG env variable.",
        metavar='"JSON or @path"'
    )

    parser.add_argument(
        '--token',
        default=os.getenv('CONSUL_ANNOUNCER_TOKEN'),
        help="Consul ACL token. "
             "You can also use CONSUL_ANNOUNCER_TOKEN env variable.",
        metavar='acl-token'
    )

    parser.add_argument(
        '--interval',
        default=os.getenv('CONSUL_ANNOUNCER_INTERVAL'),
        help="interval for periodic marking all TTL checks as passed, in seconds. "
             "Should be less than min TTL. "
             "You can also use CONSUL_ANNOUNCER_INTERVAL env variable.",
        metavar='seconds',
        type=float
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='count',
        help="verbose output. You can specify -v or -vv"
    )

    if '--' not in sys.argv:
        if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
            parser.print_help()
            sys.exit()
        else:
            parser.print_usage()
            sys.stderr.write("{}: error: command is not specified".format(parser.prog))
            sys.exit(2)

    split_at = sys.argv.index('--')
    args = parser.parse_args(sys.argv[1:split_at])
    cmd = sys.argv[split_at + 1:]

    if not args.verbose:
        root_logger.setLevel(logging.WARNING)
    elif args.verbose == 1:
        root_logger.setLevel(logging.INFO)
    elif args.verbose >= 2:
        root_logger.setLevel(logging.DEBUG)

    try:
        Service(
            agent_address=args.agent,
            config=args.config,
            cmd=cmd,
            token=args.token,
            interval=args.interval
        ).run()
    except ConnectionError as e:
        logger.error("Can't connect to \"{}\"".format(e.request.url))
        sys.exit(1)
    except (AnnouncerImproperlyConfigured, OSError, ValueError) as e:
        logger.error(e)
        sys.exit(1)
