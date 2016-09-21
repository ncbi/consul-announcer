class AnnouncerException(Exception):
    """
    Base consul-announcer exception class.
    """


class AnnouncerImproperlyConfigured(AnnouncerException):
    """
    consul-announcer is improperly configured.
    """
