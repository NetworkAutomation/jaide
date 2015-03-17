""" jaide_cli utilities for manipulating output colors. """
from colorama import Fore, init, Style
import re
import click


def color(out_string, color="success"):
    """ Highlight string for terminal color coding.

    @param out_string: the string to be colored
    @type out_string: str
    @param color: a string signifying which color to use.
    @type color: str

    @returns: the modified string, including the ANSI/win32 color codes.
    @rtype: str
    """
    init()
    if color == 'error':
        return (Fore.RED + Style.BRIGHT + out_string + Fore.RESET +
                Style.NORMAL)
    if color == 'info':
        return (Fore.YELLOW + Style.BRIGHT + out_string + Fore.RESET +
                Style.NORMAL)
    return (Fore.GREEN + Style.BRIGHT + out_string + Fore.RESET +
            Style.NORMAL)


def strip_color(search):
    """ Remove ANSI/Win32 color codes from string. """
    ansi_escape = re.compile(r'\x1b[^m]*m')
    return ansi_escape.sub('', search)


def color_diffs(output):
    """ Add color ANSI codes for diff lines. """
    output = output.replace('--- ', color('--- ', 'error'))
    output = output.replace('\n+++ ', color('\n+++ '))
    output = output.replace('\n-', color('\n-', 'error'))
    output = output.replace('\n+', color('\n+'))
    output = output.replace('\n@@ ', color('\n@@ ', 'info'))
    return output
