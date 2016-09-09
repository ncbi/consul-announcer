import signal
import subprocess

import consul


class Service(object):
    def __init__(self, agent_address, cmd_args, check_config):
        self.session = consul.Consul(agent_address.split(':', 1))
        self.process = subprocess.Popen(cmd_args)
        self.handle_signals()

    def handle_signals(self):
        for i in dir(signal):
            if i.startswith("SIG") and '_' not in i:
                signum = getattr(signal, i)
                try:
                    signal.signal(signum, self.handle_signal)
                except RuntimeError:
                    # signals that cannot be catched will raise RuntimeException (SIGKILL) ...
                    pass
                except OSError:
                    # ... or OSError (SIGSTOP)
                    pass

    def handle_signal(self, signal_number, *args):
        self.process.send_signal(signal_number)
