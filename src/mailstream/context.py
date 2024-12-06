import contextvars

_mailstream_context = contextvars.ContextVar("mailstream_client", default=None)


def with_mailstream(client):
    """Add mailstream client to context"""
    return _mailstream_context.set(client)


def from_mailstream():
    """Retrieve mailstream client from context"""
    return _mailstream_context.get()
