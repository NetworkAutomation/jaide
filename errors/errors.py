""" These are the Jaide specific exceptions that can be raised.
"""


class JaideError(Exception):
    """Base JaideErrors class for all other errors."""
    pass


class InvalidCommandError(JaideError):
    pass
