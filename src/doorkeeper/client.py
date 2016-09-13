import argparse
import logging
import sys

from doorkeeper.exceptions import DoorkeeperImproperlyConfigured
from doorkeeper.service import Service


class ArgsFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        """
        Add '-- command [arguments]' to usage.
        """
        actions.append(argparse._StoreAction(option_strings=[], dest="-- command [arguments]"))
        return super(ArgsFormatter, self).add_usage(usage, actions, groups, prefix)


def setup_logging(verbosity):
    """
    Setup logging for all 'doorkeeper.*' Python modules, based on passed verbosity level.

    :param int verbosity:
    """
    logger = logging.getLogger('doorkeeper')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s: %(message)s', datefmt='%H:%M:%S'
    ))
    logger.addHandler(handler)

    if not verbosity:
        handler.setLevel(logging.WARNING)
    elif verbosity == 1:
        handler.setLevel(logging.INFO)
    elif verbosity >= 2:
        handler.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)


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
             "Default: localhost (default agent port is 8500)",
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
        help="Polling interval",
        metavar='seconds',
        type=float
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='count',
        help="Verbose output",
    )

    if '--' not in sys.argv:
        if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
            parser.print_help()
            sys.exit()
        else:
            parser.print_usage()
            print("{}: error: command is not specified".format(parser.prog))
            sys.exit(1)

    split_at = sys.argv.index('--')
    args = parser.parse_args(sys.argv[1:split_at])
    cmd = ' '.join(sys.argv[split_at + 1:])
    setup_logging(args.verbose)

    try:
        Service(args.agent, args.config, cmd, args.interval)
    except DoorkeeperImproperlyConfigured as e:
        logger.error(e)
        sys.exit(1)
