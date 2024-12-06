class MailStreamError(Exception):
    """Base exception for mailstream package"""

    pass


class ConnectionError(MailStreamError):
    """Error during IMAP connection"""

    pass


class AuthenticationError(MailStreamError):
    """Authentication failed"""

    pass


class FetchError(MailStreamError):
    """Error fetching emails"""

    pass


class AlreadyWaitingError(MailStreamError):
    """Already waiting for updates"""

    pass
