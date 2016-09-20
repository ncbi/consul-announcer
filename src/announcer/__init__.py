import logging


# Setup logging
root_logger = logging.getLogger('announcer')
root_logger.setLevel(logging.WARNING)
root_logging_handler = logging.StreamHandler()
root_logging_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
)
root_logger.addHandler(root_logging_handler)
