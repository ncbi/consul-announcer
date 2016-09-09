import argparse
import logging
import sys

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
    if verbosity:
        logger = logging.getLogger('doorkeeper')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        if verbosity == 1:
            handler.setLevel(logging.ERROR)
        if verbosity == 2:
            handler.setLevel(logging.WARNING)
        if verbosity >= 3:
            handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)


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
    cmd_args = sys.argv[split_at + 1:]
    setup_logging(args.verbose)
    service = Service(args.agent, cmd_args, args.config)
    # TODO
