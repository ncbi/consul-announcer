import argparse
import logging
import sys

from requests.exceptions import ConnectionError

from doorkeeper import root_logging_handler
from doorkeeper.exceptions import DoorkeeperImproperlyConfigured
from doorkeeper.service import Service


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
        'consul-doorkeeper',
        description="Doorkeeper for services discovered by Consul.",
        formatter_class=ArgsFormatter
    )

    parser.add_argument(
        '--agent',
        default='localhost',
        help="Consul agent address: hostname[:port]. "
             "Default: localhost (default port is 8500)",
        metavar='hostname[:port]'
    )

    parser.add_argument(
        '--config',
        required=True,
        help="Consul checks configuration file",
        metavar='path'
    )

    parser.add_argument(
        '--interval',
        help="Interval for periodic marking all TTL checks as passed "
             "(should be less than min TTL)",
        metavar='seconds',
        type=float
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='count',
        help="Verbose output. You can specify -v or -vv"
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
        root_logging_handler.setLevel(logging.WARNING)
    elif args.verbose == 1:
        root_logging_handler.setLevel(logging.INFO)
    elif args.verbose >= 2:
        root_logging_handler.setLevel(logging.DEBUG)

    try:
        Service(args.agent, args.config, cmd, args.interval).run()
    except DoorkeeperImproperlyConfigured as e:
        logger.error(e)
        sys.exit(1)
    except ConnectionError as e:
        logger.error("Can't connect to \"{}\"".format(e.request.url))
        sys.exit(1)
