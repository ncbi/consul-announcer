import logging
import signal
import subprocess
import time

import consul

logger = logging.getLogger(__name__)


class Service(object):
    def __init__(self, agent_address, cmd_args, interval, check_config):
        logger.info("Connecting to Consul agent: {}".format(agent_address))
        self.session = consul.Consul(agent_address.split(':', 1))
        logger.info("Starting process: {}".format(' '.join(cmd_args)))
        self.process = subprocess.Popen(cmd_args)
        self.interval = interval
        self.setup()
        self.poll()
        self.tear_down()

    def handle_signals(self):
        """
        Transparently pass all the incoming signals to the invoked process.
        """
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
                except ValueError:
                    # ... can't catch signals inside a non-main thread
                    pass

    def handle_signal(self, signal_number, *args):
        self.process.send_signal(signal_number)

    def poll(self):
        """
        Check if invoked process is still running.
        """
        logger.info("Start polling the process")
        while True:
            logger.debug("Poll the process")
            time.sleep(self.interval)
            if self.process.poll() is None:
                self.update()
            else:
                logger.info("Stop polling the process")
                break

    def setup(self):
        logger.info("Registering Consul service")

    def update(self):
        pass

    def tear_down(self):
        logger.info("Deregistering Consul service")

    def __del__(self):
        """
        Cleanup on object destruction.
        """
        if self.process.poll() is None:
            logger.info("Killing the process (cleanup)")
            self.process.kill()
