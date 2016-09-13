class DoorkeeperException(Exception):
    """
    Base Doorkeeper exception class.
    """


class DoorkeeperImproperlyConfigured(DoorkeeperException):
    """
    Doorkeeper is improperly configured.
    """
